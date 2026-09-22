"""Bounded Access + Fast-Path gate; no strategy, model, broker or order imports.

Replay at most two previously captured issuers. A replay publication cutoff is
not a claim that we captured those historical bytes before the original event.
The only optional network operation refreshes each current SEC submission.
"""
from __future__ import annotations

import argparse
from datetime import date
import json
import os
from pathlib import Path
import time
import uuid

from .audit_http import ReadOnlyHTTP
from .audit_sec import SECSource
from .audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, timestamp, utc_now
from .audit_text import PARSER_VERSION, disclosure_map, parse_document, verify_comparable
from .entitlement_probe import _collect_quality, _recover_rows
from .dated_source_gate import evaluate_packet

VERSION = "access-fastpath-v1"


def source_documents(source):
    """Reject conflicting versions rather than choosing a later corrected copy."""
    by_key = {}
    for record in source.records("document"):
        if record["metadata"].get("source") != "SEC":
            continue
        old = by_key.get(record["source_key"])
        if old and old["blob_sha"] != record["blob_sha"]:
            raise AuditFailure("CONFLICTING_CAPTURED_DOCUMENT_VERSION")
        if old is None or (not old["metadata"].get("acceptance_crosschecked")
                           and record["metadata"].get("acceptance_crosschecked")):
            by_key[record["source_key"]] = record
    if not by_key or len(by_key) > 128:
        raise AuditFailure("SOURCE_DOCUMENT_COUNT_OUT_OF_BOUNDS")
    if any(not d["metadata"].get("acceptance_crosschecked") for d in by_key.values()):
        raise AuditFailure("UNCHECKED_SOURCE_ACCEPTANCE")
    return list(by_key.values())


def import_document(source, destination, record, source_head):
    meta = dict(record["metadata"], source_archive_record_id=record["id"],
                source_archive_record_hash=record["record_hash"],
                source_archive_head_hash=source_head,
                source_archive_recorded_at=record["recorded_at"], imported_at=utc_now())
    return destination.append("document", record["source_key"], meta, source.raw(record))


def prepare_snapshot(source, destination, documents, cik, cutoff, source_head):
    """Background preparation depends on issuer/cutoff, never target contents.

    SEC acceptance is a conservative prior-information boundary, not first
    publication proof. Backfill versions retain their later actual receipt time.
    """
    started, tick = utc_now(), time.monotonic()
    selected = [d for d in documents if d["metadata"]["cik"] == cik
                and timestamp(d["metadata"]["accepted_at"]) < timestamp(cutoff)]
    if not selected:
        raise AuditFailure("NO_PRE_EVENT_EVIDENCE")
    entries = []
    for record in selected:
        document = import_document(source, destination, record, source_head)
        parsed = parse_document(destination, document)
        mda = None
        if document["metadata"]["primary"] and document["metadata"]["form"] == "10-Q":
            mda = parse_document(destination, document, mda=True)
        entries.append({"parsed": parsed, "mda": mda})
    payload = {"version": VERSION, "parser_version": PARSER_VERSION,
               "parser_sha256": digest(Path(__file__).with_name("audit_text.py").read_bytes()),
               "cik": cik, "source_cutoff_exclusive": cutoff, "entries": entries}
    return destination.append("prior_snapshot", cik, {
        "version": VERSION, "started_at": started, "verified_at": utc_now(),
        "elapsed_seconds": time.monotonic() - tick, "documents": len(entries),
        "capture_semantics": "HISTORICAL_REPLAY_NOT_PROSPECTIVE",
        "source_cutoff_exclusive": cutoff, "source_archive_head_hash": source_head,
        "external_disclosure_coverage": "UNVERIFIED",
        "semantic_verification": "NOT_PERFORMED"}, canonical(payload))


def load_snapshot(store, snapshot, event_at, *, prospective=False):
    """Check pinned versions and byte hashes; never fetch missing cache entries."""
    saved = store.get(snapshot["id"])
    if saved != snapshot or saved["kind"] != "prior_snapshot":
        raise AuditFailure("SNAPSHOT_REFERENCE_MISMATCH")
    payload = strict_json(store.raw(saved))
    if (payload["version"] != VERSION or payload["parser_version"] != PARSER_VERSION
            or payload["parser_sha256"] != digest(Path(__file__).with_name("audit_text.py").read_bytes())):
        raise AuditFailure("SNAPSHOT_PARSER_VERSION_MISMATCH")
    cutoff = timestamp(event_at)
    if timestamp(payload["source_cutoff_exclusive"]) > cutoff:
        raise AuditFailure("SNAPSHOT_INCLUDES_FUTURE_KNOWLEDGE")
    if prospective and (timestamp(saved["recorded_at"]) >= cutoff
                        or timestamp(saved["metadata"]["verified_at"]) >= cutoff):
        raise AuditFailure("SNAPSHOT_NOT_PREPARED_BEFORE_EVENT")
    for entry in payload["entries"]:
        for parsed in [entry["parsed"]] + ([entry["mda"]] if entry["mda"] else []):
            doc, view = parsed["document"], parsed["view"]
            if store.get(doc["id"]) != doc or store.get(view["id"]) != view:
                raise AuditFailure("SNAPSHOT_REFERENCE_MISMATCH")
            if timestamp(doc["metadata"]["accepted_at"]) >= cutoff:
                raise AuditFailure("SNAPSHOT_INCLUDES_FUTURE_KNOWLEDGE")
            if prospective and any(timestamp(value) >= cutoff for value in (
                    doc["recorded_at"], doc["metadata"]["first_observed_at"],
                    doc["metadata"]["ingestion_complete_at"], view["recorded_at"],
                    view["metadata"]["finished_at"])):
                raise AuditFailure("PRIOR_EVIDENCE_NOT_KNOWN_AT_EVENT")
            store.raw(doc)
            if store.raw(view).decode("utf-8") != parsed["text"]:
                raise AuditFailure("SNAPSHOT_TEXT_MISMATCH")
    return payload["entries"]


def fiscal_candidates(current, priors):
    result = []
    for prior in priors:
        a, b = current["document"]["metadata"], prior["document"]["metadata"]
        if (a["cik"] != b["cik"] or b["form"] != "10-Q"
                or timestamp(b["accepted_at"]) >= timestamp(a["accepted_at"])):
            continue
        try:
            verify_comparable(current, prior)
        except AuditFailure:
            continue
        result.append(prior)
    return result


def comparator_diagnostics(source, destination, documents, source_head):
    """Measure only captured source-supported pairs; missing coverage is unknown."""
    parsed = [parse_document(destination, import_document(source, destination, d, source_head))
              for d in documents if d["metadata"]["form"] == "10-Q" and d["metadata"]["primary"]]
    pairs, unknown, ambiguous = [], 0, 0
    for current in parsed:
        candidates = fiscal_candidates(current, parsed)
        if not candidates:
            unknown += 1
            continue
        if len(candidates) != 1:
            ambiguous += 1
            continue
        a, b = current["document"], candidates[0]["document"]
        days = (date.fromisoformat(a["metadata"]["report_date"])
                - date.fromisoformat(b["metadata"]["report_date"])).days
        history = [dict(p["document"]["metadata"]) for p in parsed]
        try:
            selected = SECSource.comparator(a["metadata"], history)
            rejected = selected["accession"] != b["metadata"]["accession"]
        except AuditFailure:
            rejected = True
        pairs.append({"current": a["source_key"], "prior": b["source_key"],
                      "current_sha256": a["blob_sha"], "prior_sha256": b["blob_sha"],
                      "current_fiscal": current["fiscal"], "prior_fiscal": candidates[0]["fiscal"],
                      "day_distance": days, "old_rule_false_abstention": rejected})
    return {"pairs": pairs, "supported_pairs": len(pairs),
            "false_abstentions": sum(p["old_rule_false_abstention"] for p in pairs),
            "unpaired_due_to_capture_or_tag_coverage": unknown, "ambiguous": ambiguous,
            "production_comparator_changed": False, "population_false_rejection_rate": None}


def benchmark(source, destination, result, documents, source_head, refresh_current):
    old = result["metadata"]
    target_doc = source.get(old["document_id"])
    target_doc = next(d for d in documents if d["source_key"] == target_doc["source_key"])
    snapshot = prepare_snapshot(source, destination, documents, old["cik"], old["accepted_at"], source_head)
    stages, times = {}, {}

    def stage(name, fn):
        start, tick = utc_now(), time.monotonic()
        try:
            return fn()
        finally:
            stages[name] = time.monotonic() - tick
            times[name] = {"start": start, "end": utc_now()}

    http = ReadOnlyHTTP(destination, user_agent=os.getenv("SEC_USER_AGENT", "trading_agent read-only research audit"),
                        max_requests=3)
    target = dict(target_doc["metadata"], primary_document=target_doc["metadata"]["filename"],
                  observation_id=target_doc["metadata"]["observation_id"])
    tick = time.monotonic()
    if refresh_current:
        docs = stage("current_sec_download", lambda: SECSource(destination, http).download(target, "historical_backfill"))
        current_doc = next(d for d in docs if d["metadata"]["primary"])
        if current_doc["blob_sha"] != target_doc["blob_sha"]:
            raise AuditFailure("CURRENT_VERSION_CHANGED_SINCE_COLD_RUN")
    else:
        current_doc = stage("current_raw_replay", lambda: import_document(source, destination, target_doc, source_head))
    current = stage("current_parsing", lambda: parse_document(destination, current_doc, mda=True))
    entries = stage("warm_snapshot_load_and_hash_checks", lambda: load_snapshot(destination, snapshot, old["accepted_at"]))
    priors = [entry["mda"] for entry in entries if entry["mda"]]
    history = [p["document"]["metadata"] for p in priors]
    match = SECSource.comparator(current_doc["metadata"], history)
    prior = next(p for p in priors if p["document"]["metadata"]["accession"] == match["accession"])
    stage("fiscal_verification", lambda: verify_comparable(current, prior))
    selected = [entry["parsed"] for entry in entries
                if timestamp(entry["parsed"]["document"]["metadata"]["accepted_at"]) >= timestamp(match["accepted_at"])]
    linkage = stage("deterministic_linkage", lambda: disclosure_map(current, prior, selected))
    stages["evidence_path_total"] = time.monotonic() - tick
    def signature(links):
        return [(p["id"], p["relation"], p["new_relative_to_prior_10q"]) for p in links["links"]]
    if signature(linkage) != signature(old["prior_disclosure"]):
        raise AuditFailure("WARM_COLD_LINKAGE_MISMATCH")
    expected = {(d["source_key"], d["sha256"]) for d in old["inventory"]}
    actual = {(p["document"]["source_key"], p["document"]["blob_sha"]) for p in selected}
    if actual != expected:
        raise AuditFailure("WARM_COLD_INVENTORY_MISMATCH")
    try:
        load_snapshot(destination, snapshot, old["accepted_at"], prospective=True)
    except AuditFailure as exc:
        prospective = str(exc)
    else:
        prospective = "ACCEPTED"
    return {"cik": old["cik"], "accession": old["accession"], "current_sha256": current_doc["blob_sha"],
            "cold_source_record_id": result["id"], "cold_source_record_hash": result["record_hash"],
            "cold_original_stage_seconds": old["stage_seconds"], "warm_stage_seconds": stages,
            "warm_stage_times": times, "background_snapshot_record_id": snapshot["id"],
            "background_prepare_seconds": snapshot["metadata"]["elapsed_seconds"],
            "background_document_count": snapshot["metadata"]["documents"],
            "selected_prior_documents": len(selected), "warm_prior_network_requests": 0,
            "linkage_and_inventory_equal": True, "warm_current_network_refresh": refresh_current,
            "prospective_snapshot_check": prospective, "mode": "HISTORICAL_REPLAY",
            "excluded_latency": ["discovery", "market/status", "external-disclosure capture",
                                 "human semantic verification", "decision sealing"],
            "deadline_frozen": False}


def captured_sip_quality(source):
    """Read every captured SIP response; diagnostics cannot alter access."""
    records = [r for r in source.records("http")
               if r["source_key"].startswith("https://data.alpaca.markets/v2/stocks/quotes?")]
    from .entitlement_probe import _request_is_sip
    for record in records:
        _request_is_sip(record["source_key"])
    rows = _recover_rows(source, records, "quotes")
    statuses, frequency = 0, {}
    for record in source.records("stream_frame"):
        if record["metadata"].get("feed") != "sip":
            raise AuditFailure("SIP_FEED_NOT_ENFORCED")
        for row in strict_json(source.raw(record)):
            if row.get("T") == "s":
                statuses += 1
                key = str(row.get("z")) + ":" + str(row.get("sc"))
                frequency[key] = frequency.get(key, 0) + 1
    return {"source_integrity": source.verify(), "http_records": len(records),
            "quality": _collect_quality("quotes", rows),
            "status_rows": statuses, "status_code_frequencies_by_tape": frequency,
            "policy_frozen": False, "human_review": "REQUIRED"}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-store", action="append", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--account-observation", default="config/access_gate_observations.json")
    parser.add_argument("--sip-store")
    parser.add_argument("--refresh-current", action="store_true")
    parser.add_argument("--dated-packet", default="config/dated_source_packet.json")
    parser.add_argument("--evidence-root", default=".")
    args = parser.parse_args(argv)
    if not 1 <= len(args.source_store) <= 2:
        parser.error("at most two source stores; this is not the 50-filing audit")
    destination = EvidenceStore(args.store)
    run_id = uuid.uuid4().hex
    report = {"version": VERSION, "run_id": run_id, "started_at": utc_now(),
              "recommendation": "BLOCK_HISTORICAL_AUDIT", "blockers": [], "benchmarks": [],
              "comparator_diagnostics": [], "failures": [], "alpha_research": "NOT_RUN",
              "source_code_sha256": digest(Path(__file__).read_bytes())}
    try:
        observation = Path(args.account_observation).read_bytes()
        report["account_access"] = strict_json(observation)
        report["account_observation_record"] = destination.append("account_observation", run_id,
            {"origin": "USER_REPORTED_LOCAL_RUN", "independently_retested_here": False}, observation)["id"]
        for root in args.source_store:
            if Path(root).resolve() == Path(args.store).resolve() or not (Path(root) / "evidence.sqlite").is_file():
                raise AuditFailure("INVALID_SOURCE_ARCHIVE")
            source = EvidenceStore(root)
            try:
                integrity = source.verify()
                documents = source_documents(source)
                report["comparator_diagnostics"].append(comparator_diagnostics(source, destination, documents, integrity["head_hash"]))
                results = [r for r in source.records("audit_result") if r["metadata"].get("inventory")]
                if not results:
                    raise AuditFailure("NO_COMPLETE_COLD_BASELINE")
                # Earliest complete existing acquisition, not selected on speed or returns.
                result = min(results, key=lambda r: timestamp(r["metadata"]["accepted_at"]))
                report["benchmarks"].append(benchmark(source, destination, result, documents,
                                                      integrity["head_hash"], args.refresh_current))
            finally:
                source.close()
        if args.sip_store:
            if not (Path(args.sip_store) / "evidence.sqlite").is_file():
                raise AuditFailure("SIP_ARCHIVE_MISSING")
            source = EvidenceStore(args.sip_store)
            try:
                report["captured_sip_quality"] = captured_sip_quality(source)
            finally:
                source.close()
        else:
            report["captured_sip_quality"] = {"status": "RAW_LOCAL_ACCOUNT_SAMPLES_NOT_SUPPLIED",
                                             "policy_frozen": False}
    except (AuditFailure, OSError, KeyError, TypeError, ValueError, StopIteration) as exc:
        report["failures"].append(str(exc) if isinstance(exc, AuditFailure) else "MALFORMED_OR_MISSING_GATE_INPUT")
    finally:
        try:
            raw_packet = Path(args.dated_packet).read_bytes()
            destination.append("dated_source_packet", run_id, {}, raw_packet)
            gate = evaluate_packet(strict_json(raw_packet), args.evidence_root)
            report["dated_source_gate"] = gate
            report["recommendation"] = gate["historical_recommendation"]
            report["prospective_recommendation"] = gate["prospective_recommendation"]
            report["blockers"] = [k for k, v in gate["gates"].items()
                                  if k != "prospective_readiness" and v["status"] != "PASS"]
        except (AuditFailure, OSError, KeyError, TypeError, ValueError):
            report["blockers"] = ["DATED_SOURCE_PACKET_MISSING_OR_INVALID"]
            report["prospective_recommendation"] = "PROSPECTIVE_ACTIONABILITY_BLOCKED"
        report["finished_at"] = utc_now()
        report["evidence_integrity_before_report"] = destination.verify()
        destination.append("access_fastpath_report", run_id, report)
        path = Path(args.store) / ("access_fastpath_" + run_id + ".json")
        with path.open("x", encoding="utf-8") as handle:
            json.dump(report, handle, indent=2, allow_nan=False)
        destination.close()
    print(json.dumps({"recommendation": report["recommendation"], "blockers": report["blockers"],
                      "prospective_recommendation": report["prospective_recommendation"],
                      "failures": report["failures"], "report": str(path)}, indent=2))
    return 0 if report["recommendation"] == "RUN_50_HISTORICAL_AUDIT" and not report["failures"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
