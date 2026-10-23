"""Offline Amendment 004 frame reconciliation and priority preservation only.

Reads old evidence stores through SQLite mode=ro. No network, candidate evidence
screening, market acquisition, cohort construction or amendment changes.
"""
from contextlib import contextmanager
from datetime import date
from io import BytesIO
from pathlib import Path
import re
import sqlite3
from zipfile import ZipFile

from .acquisition_registration import (REGISTRATION_PATH, REGISTRATION_SHA,
    priority_order, registration, verify_only)
from .audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, utc_now


@contextmanager
def read_only_store(root):
    root = Path(root).resolve()
    store = EvidenceStore.__new__(EvidenceStore)
    store.root, store.objects = root, root / "objects"
    store.db = sqlite3.connect((root / "evidence.sqlite").as_uri() + "?mode=ro", uri=True)
    store.db.row_factory = sqlite3.Row
    try:
        yield store
    finally:
        store.close()


def original_rows(raw, quarter):
    """Strict metadata-only parser. Names retained for conflict checks, not rank."""
    with ZipFile(BytesIO(raw)) as archive:
        if (archive.namelist() != ["master.idx"]
                or archive.getinfo("master.idx").file_size > 40_000_000):
            raise AuditFailure("SEC_INDEX_ENTRY_OR_BYTE_CAP")
        lines = archive.read("master.idx").decode("utf-8").splitlines()
    result = []
    for number, line in enumerate(lines, 1):
        fields = line.split("|")
        if "10-Q" not in fields:
            continue
        if len(fields) != 5 or fields[2] != "10-Q":
            raise AuditFailure("MALFORMED_ORIGINAL_INDEX_ROW")
        cik, name, _, filed, path = fields
        match = re.fullmatch(r"edgar/data/([0-9]+)/([0-9]{10}-[0-9]{2}-[0-9]{6})\.txt", path)
        if (not re.fullmatch(r"[0-9]{1,10}", cik) or int(cik) == 0
                or not match or int(match[1]) != int(cik)):
            raise AuditFailure("SEC_INDEX_CIK_OR_ACCESSION_CONFLICT")
        day = date.fromisoformat(filed)
        if day.year != 2025 or (day.month - 1) // 3 + 1 != quarter:
            raise AuditFailure("SEC_INDEX_OUTSIDE_REGISTERED_QUARTER")
        result.append({"cik": cik.zfill(10), "accession": match[2],
                       "issuer_index_name": name, "filed_date": filed,
                       "path": path, "quarter": quarter, "line": number})
    return result


def reconcile(batches, preserved_pairs, expected_pairs, expected_ciks):
    unique, references = {}, {}
    for rows in batches:
        for row in rows:
            key = row["cik"], row["accession"]
            facts = {k: row[k] for k in ("cik", "accession", "issuer_index_name", "filed_date", "path")}
            if key in unique and unique[key] != facts:
                raise AuditFailure("CONFLICTING_DUPLICATE_ORIGINAL")
            unique[key] = facts
            references.setdefault(key, []).append({"quarter": row["quarter"], "line": row["line"]})
    pairs = [{"cik": k[0], "accession": k[1]} for k in sorted(unique)]
    ciks = sorted({key[0] for key in unique})
    if len(pairs) != expected_pairs or len(ciks) != expected_ciks:
        raise AuditFailure(f"FRAME_COUNT_MISMATCH:pairs={len(pairs)}/{expected_pairs};ciks={len(ciks)}/{expected_ciks}")
    if pairs != preserved_pairs:
        old = {(r["cik"], r["accession"]) for r in preserved_pairs}
        new = set(unique)
        raise AuditFailure(f"PRESERVED_PAIR_SET_OR_ORDER_MISMATCH:missing={len(old-new)};extra={len(new-old)}")
    return pairs, ciks, [{**unique[k], "index_references": references[k]} for k in sorted(unique)]


def replay(root, output):
    root, output = Path(root).resolve(), Path(output).resolve()
    verify_only(root)
    raw = (root / "research/acquisition_frame_registration_004.json").read_bytes()
    reg = registration(raw)
    frame = reg["frame"]
    report = {"version": "acquisition-frame-replay-v1", "registration_sha256": REGISTRATION_SHA,
              "started_at": utc_now(), "source_indexes": [], "store_checks": {}}
    captures, batches = [], []
    with read_only_store(root / "runs/cohort_correction_002") as old, read_only_store(root / "runs/cohort_closure_sources") as origin:
        report["store_checks"] = {"cohort_correction_002": old.verify(), "cohort_closure_sources": origin.verify()}
        for quarter, source in enumerate(frame["source_indexes"], 1):
            record = old.get(source["record_id"])
            body = old.raw(record)
            meta = record["metadata"]
            if (digest(body) != source["sha256"] or record["blob_sha"] != source["sha256"]
                    or meta["url"] != source["url"] or meta["http_status"] != 200
                    or meta["method"] != "GET" or meta.get("failure") is not None):
                raise AuditFailure("PINNED_SEC_SOURCE_PROVENANCE_MISMATCH")
            original = None
            if record["kind"] == "reused_public_source":
                if meta["original_store"] != "runs/cohort_closure_sources":
                    raise AuditFailure("UNEXPECTED_SOURCE_STORE")
                original = origin.get(meta["original_record_id"])
                if (origin.raw(original) != body
                        or any(original["metadata"][k] != meta[k] for k in ("url", "http_status", "method", "received_at", "failure"))):
                    raise AuditFailure("REUSED_SOURCE_PROVENANCE_CONFLICT")
            rows = original_rows(body, quarter)
            if len(rows) != source["original_rows"]:
                raise AuditFailure(f"QUARTER_COUNT_MISMATCH:Q{quarter}:{len(rows)}/{source['original_rows']}")
            report["source_indexes"].append({**source, "verified": True, "bytes": len(body),
                "retrieval_provenance": record, "original_retrieval_provenance": original})
            captures.append((source["quarter"], record, body))
            batches.append(rows)
        inventory_record = old.get(frame["preserved_normalized_inventory_record_id"])
        inventory_raw = old.raw(inventory_record)
        if digest(inventory_raw) != frame["preserved_normalized_inventory_sha256"]:
            raise AuditFailure("PRESERVED_INVENTORY_HASH_MISMATCH")
        inventory = strict_json(inventory_raw)
        pairs, ciks, rows = reconcile(batches, inventory["filing_inventory"]["indexed_originals"],
            frame["expected_original_index_pairs"], frame["expected_distinct_ciks"])
    order = priority_order(ciks, raw)
    # Exact canonical bytes with no trailing newline. Frame verified first;
    # preserved priority precedes any issuer-specific inspection or retrieval.
    order_raw, pair_raw = canonical(order), canonical(pairs)
    output.mkdir(parents=True, exist_ok=False)
    store = EvidenceStore(output)
    try:
        for key, record, body in captures:
            store.append("verified_frame_source", key, {"source_record": record}, body)
        store.append("verified_preserved_inventory", frame["preserved_normalized_inventory_sha256"],
                     {"source_record": inventory_record}, inventory_raw)
        store.append("reconciled_original_pairs", REGISTRATION_SHA, {"pairs": len(pairs), "ciks": len(ciks)}, pair_raw)
        store.append("reconciled_index_rows", REGISTRATION_SHA, {"metadata_only": True}, canonical(rows))
        frozen = store.append("frozen_cik_priority_order", REGISTRATION_SHA,
            {"frame_pairs_sha256": digest(pair_raw), "ciks": len(ciks), "candidate_screening_started": False}, order_raw)
        with (output / "priority_order.json").open("xb") as handle:
            handle.write(order_raw)
        report.update(status="VERIFIED", completed_at=utc_now(), original_pairs=len(pairs), distinct_ciks=len(ciks),
            normalized_pairs_sha256=digest(pair_raw), preserved_inventory_sha256=digest(inventory_raw),
            priority_order_sha256=digest(order_raw), priority_record_id=frozen["id"], priority_preserved_at=frozen["recorded_at"],
            candidate_1=order[0], substantive_candidates_reviewed=0,
            caveat="Preserved SEC index vintage, not an unrevised contemporaneous 2025 snapshot; SEC acceptance is not first public receipt.")
        store.append("frame_verification", REGISTRATION_SHA, {"status": "VERIFIED"}, canonical(report))
        report["new_store_verification"] = store.verify()
        with (output / "frame_verification.json").open("xb") as handle:
            handle.write(canonical(report))
        return report
    finally:
        store.close()


if __name__ == "__main__":
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    result = replay(REGISTRATION_PATH.parents[1], args.output)
    print(json.dumps({k: result[k] for k in ("status", "original_pairs", "distinct_ciks", "priority_order_sha256", "candidate_1")}, sort_keys=True))
