"""Metadata-only acquisition-scope freeze. Never runs the evidence audit."""
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from io import BytesIO
from pathlib import Path
import re
from zipfile import ZipFile, BadZipFile

import pytz

from .audit_market import choose_action
from .audit_store import AuditFailure, canonical, digest, timestamp, utc_now


def index_candidates(raw_indexes):
    by_cik = defaultdict(dict)
    for raw in raw_indexes:
        try:
            with ZipFile(BytesIO(raw)) as archive:
                info = archive.getinfo("master.idx")
                if info.file_size > 40_000_000 or len(archive.infolist()) != 1:
                    raise AuditFailure("SEC_INDEX_BYTE_OR_ENTRY_CAP")
                text = archive.read(info).decode("utf-8")
        except (BadZipFile, KeyError, UnicodeError):
            raise AuditFailure("INVALID_SEC_QUARTER_INDEX") from None
        for line in text.splitlines():
            fields = line.split("|")
            if len(fields) != 5 or fields[2] != "10-Q":
                continue
            cik, name, form, filed, path = fields
            if not cik.isdigit() or not re.fullmatch(r"edgar/data/\d+/\d{10}-\d{2}-\d{6}\.txt", path):
                raise AuditFailure("INVALID_SEC_INDEX_ROW")
            if not date(2025, 1, 1) <= date.fromisoformat(filed) <= date(2025, 6, 30):
                raise AuditFailure("INDEX_OUTSIDE_REGISTERED_WINDOW")
            cik, accession = cik.zfill(10), path.rsplit("/", 1)[1][:-4]
            by_cik[cik][accession] = dict(cik=cik, issuer_index_name=name, form=form,
                                        filed_date=filed, accession=accession)
    candidates = sorted(cik for cik, rows in by_cik.items() if len(rows) >= 2)[:25]
    if len(candidates) != 25:
        raise AuditFailure("INSUFFICIENT_REGISTERED_ISSUERS_NO_REPLACEMENT")
    return {cik: list(by_cik[cik].values()) for cik in candidates}


def sessions_2025h1():
    """Frozen calendar facts, to be pinned to official calendar/closure evidence."""
    closed = {"2025-01-01", "2025-01-09", "2025-01-20", "2025-02-17",
              "2025-04-18", "2025-05-26", "2025-06-19", "2025-07-04"}
    eastern = pytz.timezone("America/New_York")
    day, result = date(2025, 1, 1), []
    while day <= date(2025, 7, 7):
        if day.weekday() < 5 and day.isoformat() not in closed:
            opening = eastern.localize(datetime.combine(day, datetime.min.time()).replace(hour=9, minute=30))
            closing = opening.replace(hour=13 if day.isoformat() == "2025-07-03" else 16, minute=0)
            result.append((opening.astimezone(pytz.UTC), closing.astimezone(pytz.UTC)))
        day += timedelta(days=1)
    return result


def build_scope(candidates, filing_metadata, registration_sha, calendar_refs):
    targets = []
    for cik in candidates:
        indexed = {r["accession"] for r in candidates[cik]}
        rows = sorted([r for r in filing_metadata[cik] if r["form"] == "10-Q"
                       and date(2025, 1, 1) <= timestamp(r["accepted_at"]).date() <= date(2025, 6, 30)],
                      key=lambda r: (timestamp(r["accepted_at"]), r["accession"]))
        if {r["accession"] for r in rows} != indexed:
            raise AuditFailure("INDEX_SUBMISSIONS_MISMATCH_NO_REPLACEMENT:" + cik)
        for row in rows[:2]:
            ready = timestamp(row["accepted_at"]) + timedelta(seconds=600)
            targets.append({"cik": cik, "accession": row["accession"], "form": "10-Q",
                "accepted_at": row["accepted_at"], "actionable_at": choose_action(ready.isoformat(), sessions_2025h1()),
                "instrument_id": "research:cik-" + cik + "-common-001",
                "instrument_id_authority": "INTERNAL_RESEARCH",
                "class_binding": "RESERVED_PENDING_SOURCE_LINEAGE_REVIEW",
                "report_date": row["report_date"], "metadata_observation_id": row["observation_id"]})
    if len(targets) != 50 or len(Counter(t["cik"] for t in targets)) != 25:
        raise AuditFailure("INVALID_FROZEN_COHORT_SIZE")
    return {"status": "FROZEN", "registration_sha256": registration_sha,
            "window": {"start": "2025-01-01", "end": "2025-06-30"},
            "selection": "25 lowest numeric CIKs with at least two indexed original 10-Qs; earliest acceptance then accession, two each",
            "no_replacement": True, "historical_deadline_seconds": 600,
            "deadline_semantics": "Fixed acquisition scenario only; not a measured or frozen alpha-processing deadline",
            "availability_anchor": "SIMULATED_FROM_SEC_ACCEPTANCE_NOT_HISTORICAL_RECEIPT",
            "calendar_evidence": calendar_refs, "targets": targets,
            "context_instruments": [{"cik": "0000884394", "symbol": "SPY",
                "instrument_id": "research:cik-0000884394-unit-001", "actionable_at": at}
                for at in sorted({t["actionable_at"] for t in targets})]}


def freeze_scope(scope, store, output):
    path = Path(output)
    if path.exists():
        raise AuditFailure("COHORT_ALREADY_FROZEN_EXPLICIT_AMENDMENT_REQUIRED")
    sha = digest(canonical(scope))
    document = {"version": "historical-cohort-v1", "frozen_at": utc_now(), "scope_sha256": sha,
                "scope": scope, "amendment": None, "audit_executed": False}
    raw = canonical(document)
    record = store.append("frozen_cohort_manifest", sha, {"scope_sha256": sha}, raw)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as handle:
        handle.write(raw + b"\n")
    return {"record_id": record["id"], "scope_sha256": sha,
            "file_sha256": digest(raw + b"\n"), "path": str(path)}
