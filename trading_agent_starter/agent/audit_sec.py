"""Deterministic SEC discovery and complete-submission download, bounded by caps."""
from __future__ import annotations

from datetime import date, datetime
import re

import pytz

from .audit_store import AuditFailure, VERSION, digest, strict_json, timestamp, utc_now

# Transition reports are prior-disclosure evidence, never original 10-Q targets
# or ordinary same-quarter comparators. Keep the latter selections unchanged.
FORMS = {"10-Q", "10-Q/A", "10-K", "10-K/A", "8-K", "8-K/A",
         "10-QT", "10-QT/A", "10-KT", "10-KT/A"}
ACCESSION = re.compile(r"\d{10}-\d{2}-\d{6}\Z")
FILENAME = re.compile(r"[A-Za-z0-9_.-]+\Z")


def safe_name(value):
    if not isinstance(value, str) or not FILENAME.fullmatch(value) or ".." in value:
        raise AuditFailure("UNSAFE_SEC_FILENAME")
    return value


class SECSource:
    def __init__(self, store, http, *, max_history_pages=8, max_prior_filings=64):
        self.store, self.http = store, http
        self.max_history_pages, self.max_prior_filings = max_history_pages, max_prior_filings
        self.cache = {}

    def discover(self, cik, start, end):
        if not re.fullmatch(r"\d{1,10}", str(cik)):
            raise AuditFailure("INVALID_CIK")
        cik = str(int(cik)).zfill(10)
        if not date(2016, 1, 1) <= start <= end <= date.today():
            raise AuditFailure("INVALID_DISCOVERY_RANGE")
        record = self.http.get(f"https://data.sec.gov/submissions/CIK{cik}.json", max_bytes=10_000_000)
        root = strict_json(self.store.raw(record))
        if str(int(root.get("cik", -1))).zfill(10) != cik:
            raise AuditFailure("SEC_CIK_MISMATCH")
        try:
            recent, pages = root["filings"]["recent"], root["filings"]["files"]
            needed = [p for p in pages if date.fromisoformat(p["filingTo"]) >= start
                      and date.fromisoformat(p["filingFrom"]) <= end]
        except (KeyError, TypeError, ValueError):
            raise AuditFailure("MALFORMED_SEC_HISTORY") from None
        if len(needed) > self.max_history_pages:
            raise AuditFailure("SEC_HISTORY_PAGE_CAP")
        batches = [(recent, record)]
        for page in needed:
            name = safe_name(page["name"])
            if not name.startswith(f"CIK{cik}-submissions-"):
                raise AuditFailure("SEC_HISTORY_CIK_MISMATCH")
            response = self.http.get(f"https://data.sec.gov/submissions/{name}", max_bytes=10_000_000)
            batches.append((strict_json(self.store.raw(response)), response))
        filings = {}
        for data, response in batches:
            fields = ("accessionNumber", "form", "reportDate", "acceptanceDateTime", "primaryDocument")
            if not isinstance(data, dict) or not all(isinstance(data.get(k), list) for k in fields):
                raise AuditFailure("MALFORMED_SEC_COLUMNS")
            if len({len(data[k]) for k in fields}) != 1:
                raise AuditFailure("MISALIGNED_SEC_COLUMNS")
            for acc, form, report, accepted, primary in zip(*(data[k] for k in fields)):
                if form not in FORMS:
                    continue
                if not isinstance(acc, str) or not ACCESSION.fullmatch(acc):
                    raise AuditFailure("INVALID_ACCESSION")
                accepted_dt = timestamp(accepted)
                if not start <= accepted_dt.date() <= end:
                    continue
                safe_name(primary)
                if report:
                    try:
                        date.fromisoformat(report)
                    except ValueError:
                        raise AuditFailure("INVALID_REPORT_DATE") from None
                row = dict(cik=cik, accession=acc, form=form, report_date=report,
                           accepted_at=accepted, primary_document=primary)
                if acc in filings and any(filings[acc][k] != v for k, v in row.items()):
                    raise AuditFailure("CONFLICTING_SEC_METADATA")
                key = f"{cik}/{acc}"
                seen = self.store.records("filing_observation", key)
                observation = self.store.append("filing_observation", key, dict(
                    row, source_record=response["id"],
                    first_observed_at=(seen[0]["metadata"]["first_observed_at"] if seen
                                       else response["metadata"]["received_at"]),
                    timestamp_semantics="SEC acceptance, not first public disclosure",
                    source_publication_at=None, version=VERSION))
                filings[acc] = dict(row, observation_id=observation["id"],
                                    first_observed_at=observation["metadata"]["first_observed_at"])
        return sorted(filings.values(), key=lambda f: (timestamp(f["accepted_at"]), f["accession"]))

    @staticmethod
    def comparator(target, filings):
        if not target["report_date"]:
            raise AuditFailure("MISSING_REPORT_DATE")
        report = date.fromisoformat(target["report_date"])
        candidates = [f for f in filings if f["form"] == "10-Q" and f["report_date"]
                      and timestamp(f["accepted_at"]) < timestamp(target["accepted_at"])
                      and 350 <= (report - date.fromisoformat(f["report_date"])).days <= 380]
        if len(candidates) != 1:
            raise AuditFailure("MISSING_OR_AMBIGUOUS_PRIOR_QUARTER")
        return candidates[0]

    def prior_filings(self, target, comparator, filings):
        selected = [f for f in filings if timestamp(comparator["accepted_at"]) <= timestamp(f["accepted_at"])
                    < timestamp(target["accepted_at"])]
        if len(selected) > self.max_prior_filings:
            raise AuditFailure("PRIOR_DISCLOSURE_CAP_EXCEEDED")
        return selected

    def download(self, filing, mode):
        acc, cik = filing["accession"], filing["cik"]
        if not ACCESSION.fullmatch(acc) or not re.fullmatch(r"\d{10}", cik):
            raise AuditFailure("INVALID_FILING_ID")
        cache_key = cik, acc, mode
        if cache_key in self.cache:
            self.store.append("acquisition_cache_hit", f"{cik}/{acc}", {
                "document_ids": [d["id"] for d in self.cache[cache_key]], "at": utc_now()})
            return self.cache[cache_key]
        url = f"https://www.sec.gov/Archives/edgar/data/{int(cik)}/{acc.replace('-', '')}/{acc}.txt"
        response = self.http.get(url)
        raw = self.store.raw(response)
        header = raw.split(b"<DOCUMENT>", 1)[0]
        acceptance = re.search(rb"<ACCEPTANCE-DATETIME>(\d{14})", header)
        accession_header = re.search(rb"ACCESSION NUMBER:\s*([\d-]+)", header)
        cik_header = re.search(rb"CENTRAL INDEX KEY:\s*(\d+)", header)
        form_header = re.search(rb"CONFORMED SUBMISSION TYPE:\s*([^\r\n]+)", header)
        if not all((acceptance, accession_header, cik_header, form_header)):
            raise AuditFailure("SEC_ENVELOPE_PROVENANCE_MISSING")
        try:
            header_time = pytz.timezone("America/New_York").localize(
                datetime.strptime(acceptance[1].decode(), "%Y%m%d%H%M%S"), is_dst=None)
            if (accession_header[1].decode() != acc or int(cik_header[1]) != int(cik)
                    or form_header[1].decode().strip() != filing["form"]
                    or abs((header_time - timestamp(filing["accepted_at"])).total_seconds()) >= 1):
                raise AuditFailure("SEC_ENVELOPE_METADATA_CONFLICT")
        except (ValueError, UnicodeError, pytz.InvalidTimeError):
            raise AuditFailure("SEC_ENVELOPE_TIMESTAMP_AMBIGUOUS") from None
        # The SEC envelope is SGML. Never render it or follow embedded links.
        matches = list(re.finditer(rb"<DOCUMENT>\s*(.*?)</DOCUMENT>", raw, re.I | re.S))
        if not matches or len(matches) > 256:
            raise AuditFailure("MALFORMED_OR_OVERSIZE_SEC_ENVELOPE")
        documents, found_primary = [], False
        for match in matches:
            block = match.group(1)
            kind = re.search(rb"<TYPE>\s*([^\r\n<]+)", block, re.I)
            name = re.search(rb"<FILENAME>\s*([^\r\n<]+)", block, re.I)
            body = re.search(rb"<TEXT>\s*(.*?)\s*</TEXT>", block, re.I | re.S)
            if not (kind and name and body):
                raise AuditFailure("MALFORMED_SEC_DOCUMENT")
            try:
                filename = safe_name(name.group(1).decode("ascii").strip())
                doc_type = kind.group(1).decode("ascii").strip()
            except UnicodeError:
                raise AuditFailure("INVALID_SEC_DOCUMENT_NAME") from None
            primary = filename == filing["primary_document"]
            if not primary and not doc_type.startswith("EX-99"):
                continue
            if len(documents) >= 20:
                raise AuditFailure("SEC_EXHIBIT_CAP_EXCEEDED")
            if primary and (found_primary or doc_type != filing["form"]):
                raise AuditFailure("CONFLICTING_SEC_PRIMARY")
            found_primary |= primary
            start = match.start(1) + body.start(1)
            key = f"{cik}/{acc}/{filename}"
            same_bytes = [r for r in self.store.records("document", key)
                          if r["blob_sha"] == digest(body.group(1))]
            first_observed = (same_bytes[0]["metadata"]["first_observed_at"] if same_bytes
                              else response["metadata"]["received_at"])
            child = self.store.append("document", key, {
                "version": VERSION, "source": "SEC", "source_url": url,
                "cik": cik, "accession": acc, "filename": filename, "form": doc_type,
                "report_date": filing["report_date"], "primary": primary,
                "accepted_at": filing["accepted_at"], "source_publication_at": None,
                "header_acceptance_local": acceptance[1].decode(),
                "header_timezone": "America/New_York", "acceptance_crosschecked": True,
                "first_observed_at": first_observed,
                "event_first_observed_at": filing["first_observed_at"],
                "download_received_at": response["metadata"]["received_at"],
                "ingestion_complete_at": utc_now(), "capture_mode": mode,
                "http_record": response["id"], "observation_id": filing["observation_id"],
                "parent_byte_span": [start, start + len(body.group(1))],
                "original_public_version_guaranteed": False,
                "untrusted": True}, body.group(1))
            documents.append(child)
        if not found_primary:
            raise AuditFailure("SEC_PRIMARY_DOCUMENT_MISSING")
        self.cache[cache_key] = documents
        return documents
