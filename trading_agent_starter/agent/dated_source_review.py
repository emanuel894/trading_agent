"""Offline diagnostics of captured public sources and owner SIP archives.

No downloading, execution, forecasting, or automatic promotion of a policy.
The deliberately selected fiscal sample is not a population estimate.
"""
from __future__ import annotations

import argparse
from datetime import date
from html.parser import HTMLParser
import json
from pathlib import Path
import uuid

from .access_fastpath import captured_sip_quality
from .audit_store import AuditFailure, EvidenceStore, canonical, digest, utc_now
from .audit_text import verify_comparable
from .entitlement_probe import _collect_quality, _recover_rows
from .source_probe import parse_halt_rss

SAMPLE = ("0000909832-23-000065", "0000909832-22-000035", "0000909832-23-000042",
          "0001336917-22-000017", "0001336917-22-000029", "0001336917-21-000040")


class CoverTags(HTMLParser):
    """Keep context references; never zip unrelated share-class tags together."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.rows, self.active = [], None

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        name = attrs.get("name", "").split(":")[-1]
        if tag == "ix:nonnumeric" and name in {
                "EntityRegistrantName", "Security12bTitle", "TradingSymbol", "SecurityExchangeName"}:
            if self.active:
                raise AuditFailure("NESTED_IDENTITY_TAG")
            self.active = dict(tag=name, context_ref=attrs.get("contextref"), text="")

    def handle_data(self, data):
        if self.active is not None:
            self.active["text"] += data

    def handle_endtag(self, tag):
        if tag == "ix:nonnumeric" and self.active is not None:
            self.active["text"] = " ".join(self.active["text"].split())
            self.rows.append(self.active)
            self.active = None


def fiscal_review(source):
    selected = {}
    for accession in SAMPLE:
        docs = [r for r in source.records("document")
                if r["metadata"].get("accession") == accession and r["metadata"].get("primary")]
        if len(docs) != 1 or not docs[0]["metadata"].get("acceptance_crosschecked"):
            raise AuditFailure("FISCAL_SAMPLE_MISSING_OR_AMBIGUOUS:" + accession)
        doc = docs[0]
        views = source.records("text_view", doc["id"])
        if len(views) != 1:
            raise AuditFailure("FISCAL_SAMPLE_VIEW_MISSING_OR_AMBIGUOUS")
        view = views[0]
        selected[accession] = {"document": doc, "view": view,
                               "fiscal": view["metadata"]["fiscal"]}
    pairs = []
    for current, prior in [(SAMPLE[0], SAMPLE[1]), (SAMPLE[4], SAMPLE[5])]:
        a, b = selected[current], selected[prior]
        days = (date.fromisoformat(a["document"]["metadata"]["report_date"])
                - date.fromisoformat(b["document"]["metadata"]["report_date"])).days
        try:
            verify_comparable(a, b)
            fiscal_ok = True
        except AuditFailure:
            fiscal_ok = False
        pairs.append({"current": current, "prior": prior, "day_distance": days,
                      "current_fiscal": a["fiscal"], "prior_fiscal": b["fiscal"],
                      "day_prefilter_accepts": 350 <= days <= 380,
                      "source_tag_comparable": fiscal_ok,
                      "false_abstention_from_day_prefilter": fiscal_ok and not 350 <= days <= 380})
    docs = []
    for accession, p in selected.items():
        doc, view = p["document"], p["view"]
        text = source.raw(view).decode("utf-8")
        needles = ["53-week", "52/53", "52 or 53", "fiscal year end", "transition period",
                   "no fiscal 2022", "12 weeks", "12-week"]
        spans = []
        for needle in needles:
            start = text.lower().find(needle)
            if start >= 0:
                spans.append({"search_phrase": needle, "span": [max(0, start - 120), min(len(text), start + 300)]})
        cover = CoverTags()
        cover.feed(source.raw(doc).decode("utf-8"))
        docs.append({"accession": accession, "cik": doc["metadata"]["cik"],
                     "form": doc["metadata"]["form"], "accepted_at": doc["metadata"]["accepted_at"],
                     "report_date": doc["metadata"]["report_date"], "fiscal": p["fiscal"],
                     "url": doc["metadata"]["source_url"], "document_id": doc["id"],
                     "raw_sha256": doc["blob_sha"], "view_id": view["id"],
                     "text_sha256": view["blob_sha"], "review_spans": spans,
                     "cover_tags": cover.rows, "cover_tags_prove_full_active_interval": False})
    return {"documents": docs, "pairs": pairs, "selected_issuers": 2,
            "legitimate_comparator_pairs": sum(p["source_tag_comparable"] for p in pairs),
            "measured_day_prefilter_false_abstentions": sum(p["false_abstention_from_day_prefilter"] for p in pairs),
            "population_false_abstention_rate": None,
            "decision": "KEEP_350_380_AND_FISCAL_TAG_VERIFICATION; CAPTURE_TRANSITION_DISCLOSURES; TRANSITION_REVIEW_REQUIRED",
            "transition_tags_alone_prove_comparability": False}


def public_review(source):
    source.verify()
    captures, halts = [], []
    for record in source.records("public_source"):
        meta = record["metadata"]
        captures.append({"id": record["id"], "key": record["source_key"],
                         "sha256": record["blob_sha"], **meta})
        if "nasdaqtrader.com/rss.aspx?" in meta["url"] and meta.get("http_status") == 200 and not meta.get("failure"):
            parsed = parse_halt_rss(source.raw(record))
            halts.append({"record_id": record["id"], "sha256": record["blob_sha"], "url": meta["url"],
                          **{k: v for k, v in parsed.items() if k != "rows"}})
    return {"captures": captures, "halt_diagnostics": halts, "fiscal_review": fiscal_review(source),
            "source_integrity": source.verify(), "policy_frozen": False}


def sip_review(source):
    report = captured_sip_quality(source)
    counts = report["quality"]["total_rows_by_symbol"]
    count = sum(counts.values())
    if not report["http_records"] or not count:
        return {"status": "UNRESOLVED", "reason": "NO_CAPTURED_SIP_QUOTE_ROWS",
                "source_integrity": report["source_integrity"], "data_quality": None,
                "historical_entitlement_changed": False, "policy_frozen": False}
    quality = report.pop("quality")
    quality["strict_policy_pass_rate_at_row_timestamp"] = quality["strict_execution_quality_pass_rows"] / count
    quality["strict_policy_pass_rate_by_symbol"] = {
        s: quality["strict_execution_quality_pass_rows_by_symbol"][s] / n if n else None for s, n in counts.items()}
    records = [r for r in source.records("http")
               if r["source_key"].startswith("https://data.alpaca.markets/v2/stocks/quotes?")]
    rows = _recover_rows(source, records, "quotes")
    by_symbol = {}
    for symbol, values in rows.items():
        part = _collect_quality("quotes", {symbol: values})
        part["strict_policy_pass_rate_at_row_timestamp"] = (
            part["strict_execution_quality_pass_rows"] / len(values) if values else None)
        part["zero_fields"] = {field: sum(isinstance(row, dict) and row.get(field) == 0
                                          for row, _, _ in values) for field in ("bp", "ap", "bs", "as")}
        by_symbol[symbol] = part
    return {"status": "MEASURED_REVIEW_REQUIRED", "data_quality": quality, **report,
            "data_quality_by_symbol": by_symbol,
            "quote_response_hashes": [{"record_id": r["id"], "sha256": r["blob_sha"]} for r in records],
            "scope": "ALL_CAPTURED_PAGES_IN_SUPPLIED_ARCHIVE; NOT_A_POPULATION_SAMPLE",
            "repeated_requests_may_repeat_observations": True,
            "historical_entitlement_changed": False,
            "row_timestamp_pass_is_not_actionability_pass": True}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-store", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--kind", choices=("public", "sip"), required=True)
    args = parser.parse_args(argv)
    run_id = uuid.uuid4().hex
    destination = EvidenceStore(args.store)
    try:
        if (Path(args.source_store).resolve() == Path(args.store).resolve()
                or not (Path(args.source_store) / "evidence.sqlite").is_file()):
            raise AuditFailure("INVALID_SOURCE_ARCHIVE")
        source = EvidenceStore(args.source_store)
        try:
            report = public_review(source) if args.kind == "public" else sip_review(source)
        finally:
            source.close()
        report.update(reviewed_at=utc_now(), version="dated-source-review-v1",
                      review_code_sha256=digest(Path(__file__).read_bytes()))
    except (AuditFailure, OSError, ValueError, KeyError, TypeError) as exc:
        report = {"status": "UNRESOLVED", "failure": str(exc) if isinstance(exc, AuditFailure)
                  else "MALFORMED_OR_MISSING_REVIEW_INPUT", "policy_frozen": False}
    record = destination.append("dated_source_review", run_id, {"kind": args.kind}, canonical(report))
    path = Path(args.store) / ("dated_source_review_" + run_id + ".json")
    with path.open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2, allow_nan=False)
    destination.verify()
    destination.close()
    print(json.dumps({"report": str(path), "record_id": record["id"], "sha256": record["blob_sha"],
                      "status": report.get("status", "MEASURED_REVIEW_REQUIRED")}, indent=2))
    return 2 if report.get("status") == "UNRESOLVED" else 0


if __name__ == "__main__":
    raise SystemExit(main())
