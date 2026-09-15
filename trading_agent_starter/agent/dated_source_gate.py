"""Evidence-backed historical research gates; prospective readiness is separate.

Reviews are explicit human/source assertions, not automatic legal or completeness
proof. A true assertion needs a scoped reviewer and available hash-verified
evidence. Missing evidence is UNRESOLVED; known contradictions are FAIL.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import uuid

from .audit_market import validate_quote
from .audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, timestamp, utc_now

VERSION = "dated-source-gate-v1"
CRITERIA = {
    "historical_sip_access": ("bars_rows", "quotes_rows", "sip_only", "no_provider_restriction"),
    "instrument_identity": ("dated_intervals", "share_class_lineage", "scope_coverage"),
    "lifecycle": ("listing_delisting_bounds", "ticker_name_changes", "scope_coverage"),
    "corporate_actions": ("splits", "mergers_reorganizations", "distributions_class_changes",
                          "announcement_effective_separate", "no_unresolved_conflicts"),
    "historical_halt_tradability": ("known_sessions", "halt_history_coverage", "carry_in_resolved",
                                     "suspension_coverage", "rule_registered", "nbbo_context_available"),
    "source_rights": ("terms_snapshots", "internal_research_use", "automated_retrieval",
                      "retention", "redistribution_restrictions_recorded"),
    "quote_policy_review": ("real_sample_review", "provider_definitions_review", "policy_frozen"),
    "fiscal_comparator_review": ("real_53_week_sample", "real_transition_sample",
                                 "week_based_sample", "rule_decision_registered"),
    "prospective_readiness": ("realtime_sip", "live_status", "pre_event_warm_evidence",
                              "decision_receipt_cutoff", "clock_and_continuity"),
}
HISTORICAL = tuple(k for k in CRITERIA if k != "prospective_readiness")
SCOPED = {"instrument_identity", "lifecycle", "corporate_actions", "historical_halt_tradability", "source_rights"}


def combine(values):
    return "FAIL" if "FAIL" in values else "UNRESOLVED" if "UNRESOLVED" in values or not values else "PASS"


def evidence_inventory(packet, root):
    root = Path(root).resolve()
    result = {}
    for source in packet.get("evidence", []):
        key = source["id"]
        if key in result:
            raise AuditFailure("DUPLICATE_PACKET_EVIDENCE_ID")
        item = {"status": "UNRESOLVED", "reason": "EVIDENCE_UNAVAILABLE", "source": source}
        try:
            path = (root / source["path"]).resolve()
            if not path.is_relative_to(root) or not re.fullmatch(r"[a-f0-9]{64}", source["sha256"]):
                raise AuditFailure("INVALID_PACKET_EVIDENCE_PATH_OR_HASH")
            if path.is_file():
                if path.stat().st_size > 40_000_000:
                    raise AuditFailure("PACKET_EVIDENCE_BYTE_CAP")
                if digest(path.read_bytes()) != source["sha256"]:
                    item.update(status="FAIL", reason="PACKET_EVIDENCE_HASH_MISMATCH")
                elif source.get("kind") in {"official_capture", "owner_local_observation", "source_review"}:
                    item.update(status="PASS", reason=None)
        except OSError:
            pass
        result[key] = item
    return result


def valid_scope(scope):
    """The proposal is a source-validation scope, not a performed audit."""
    targets = scope.get("targets", [])
    if len(targets) != 50 or len({t.get("cik") for t in targets}) < 25:
        return False
    keys = [t.get("accession") for t in targets]
    if None in keys or len(set(keys)) != len(keys):
        return False
    try:
        for target in targets:
            if (not re.fullmatch(r"\d{10}", target["cik"])
                    or not re.fullmatch(r"\d{10}-\d{2}-\d{6}", target["accession"])
                    or not target["instrument_id"].startswith("research:")):
                return False
            timestamp(target["actionable_at"])
        contexts = scope.get("context_instruments", [])
        needed = {timestamp(t["actionable_at"]) for t in targets}
        covered = {timestamp(t["actionable_at"]) for t in contexts if t.get("symbol") == "SPY"
                   and re.fullmatch(r"\d{10}", t["cik"]) and t["instrument_id"].startswith("research:")}
        if not needed.issubset(covered):
            return False
    except (KeyError, AuditFailure):
        return False
    return True


def review_gate(name, review, scope_sha, evidence):
    criteria, reasons = {}, []
    for key in CRITERIA[name]:
        item = review.get("criteria", {}).get(key, {})
        value = item.get("value")
        refs = item.get("evidence_ids", [])
        verified = [evidence.get(ref, {"status": "UNRESOLVED"})["status"] for ref in refs]
        if value is False:
            status = "FAIL"
        elif value is not True:
            status = "UNRESOLVED"
        elif (not review.get("reviewed_by") or not review.get("reviewed_at")
              or not item.get("rationale") or not refs):
            status = "UNRESOLVED"
        elif name in SCOPED and review.get("scope_sha256") != scope_sha:
            status = "UNRESOLVED"
        else:
            timestamp(review["reviewed_at"])
            status = combine(verified)
            # Owner attestations can establish reported account access, not
            # historical lifecycle, quote quality or licensing completeness.
            if name != "historical_sip_access" and any(
                    evidence.get(ref, {}).get("source", {}).get("kind") == "owner_local_observation" for ref in refs):
                status = "UNRESOLVED"
        criteria[key] = status
        if status != "PASS":
            reasons.append(key + ":" + (item.get("rationale") or "MISSING_REVIEW_OR_EVIDENCE"))
    return {"status": combine(list(criteria.values())), "criteria": criteria, "reasons": reasons}


def identity_failures(packet):
    intervals = packet.get("instrument_intervals", [])
    failures = []
    for row in intervals:
        required = ("instrument_id", "cik", "issuer", "share_class", "ticker", "exchange",
                    "valid_from", "valid_to", "lineage_id", "id_authority", "evidence_ids")
        if not all(row.get(k) for k in required):
            failures.append("INCOMPLETE_INSTRUMENT_INTERVAL")
            continue
        if (row["id_authority"] != "INTERNAL_RESEARCH" or not row["instrument_id"].startswith("research:")
                or not re.fullmatch(r"\d{10}", row["cik"])):
            failures.append("INSTRUMENT_ID_AUTHORITY_MISREPRESENTED")
        if timestamp(row["valid_from"]) >= timestamp(row["valid_to"]):
            failures.append("INVALID_INSTRUMENT_INTERVAL")
    for target in (packet.get("scope", {}).get("targets", [])
                   + packet.get("scope", {}).get("context_instruments", [])):
        at = timestamp(target["actionable_at"])
        matches = [r for r in intervals if r.get("instrument_id") == target["instrument_id"]
                   and r.get("cik") == target["cik"] and r.get("valid_from") and r.get("valid_to")
                   and (not target.get("symbol") or r.get("ticker") == target["symbol"])
                   and timestamp(r["valid_from"]) <= at < timestamp(r["valid_to"])]
        if len(matches) != 1:
            failures.append("MISSING_OR_OVERLAPPING_IDENTITY_INTERVAL:" + target.get("accession", target["instrument_id"]))
    # Reusing a ticker for a different class must not merge internal lineages.
    lineages = {}
    for row in intervals:
        key = row.get("instrument_id")
        lineage = (row.get("cik"), row.get("lineage_id"))
        if key in lineages and lineages[key] != lineage:
            failures.append("INTERNAL_ID_REUSED_FOR_DIFFERENT_LINEAGE")
        lineages[key] = lineage
    return sorted(set(failures))


def historical_tradability(*, at, listing, session, quote, halts, coverage, conflicts):
    """Research reconstruction. No live stream, future bars, returns or fills.

    `halts` must include carry-in suspensions; coverage is an independently
    reviewed assertion. Scheduled resumption alone does not close an interval.
    """
    action = timestamp(at)
    failed, unresolved = [], []
    if coverage.get("feed") != "sip":
        failed.append("SIP_FEED_NOT_ENFORCED")
    if not coverage.get("source_record_ids"):
        unresolved.append("MARKET_PROVENANCE_MISSING")
    if not timestamp(listing["valid_from"]) <= action < timestamp(listing["valid_to"]):
        failed.append("OUTSIDE_ACTIVE_LISTING_INTERVAL")
    if not timestamp(session["open"]) <= action < timestamp(session["close"]):
        failed.append("OUTSIDE_KNOWN_REGULAR_SESSION")
    for field in ("date_scope_complete", "market_scope_complete", "carry_in_resolved", "suspensions_reviewed"):
        if coverage.get(field) is not True:
            unresolved.append("HALT_COVERAGE_UNRESOLVED:" + field)
    for halt in halts:
        if timestamp(halt["halt_at"]) > action:
            continue
        resume = halt.get("actual_trade_resume_at")
        if resume and halt.get("resume_authoritative") is True:
            if timestamp(resume) <= timestamp(halt["halt_at"]):
                failed.append("INVALID_HALT_INTERVAL")
            elif action < timestamp(resume):
                failed.append("AUTHORITATIVE_HALT_COVERS_ACTION")
        elif halt.get("scheduled_trade_resume_at") and timestamp(halt["scheduled_trade_resume_at"]) <= action:
            unresolved.append("SCHEDULED_RESUMPTION_NOT_CONFIRMED")
        else:
            failed.append("OPEN_HALT_OR_SUSPENSION_COVERS_ACTION")
    for conflict in conflicts:
        if timestamp(conflict["valid_from"]) <= action < timestamp(conflict["valid_to"]):
            unresolved.append("UNRESOLVED_LIFECYCLE_CONFLICT")
    try:
        validate_quote(quote, at)
    except AuditFailure as exc:
        failed.append(str(exc))
    status = "FAIL" if failed else "UNRESOLVED" if unresolved else "PASS"
    return {"status": status, "label": "HISTORICAL_TRADABILITY_RECONSTRUCTION",
            "live_status": False, "original_receipt_proven": False,
            "decision_time_eligibility": "NOT_EVALUATED",
            "failed": sorted(set(failed)), "unresolved": sorted(set(unresolved))}


def evaluate_packet(packet, root):
    if packet.get("version") != VERSION or set(packet.get("reviews", {})) - set(CRITERIA):
        raise AuditFailure("INVALID_DATED_PACKET_SCHEMA")
    scope = packet.get("scope", {})
    scope_sha = digest(canonical(scope))
    evidence = evidence_inventory(packet, root)
    gates = {name: review_gate(name, packet.get("reviews", {}).get(name, {}), scope_sha, evidence)
             for name in CRITERIA}
    scope_ok = valid_scope(scope)
    if not scope_ok:
        for name in SCOPED:
            if gates[name]["status"] == "PASS":
                gates[name]["status"] = "UNRESOLVED"
            gates[name]["reasons"].append("PROPOSED_COHORT_SCOPE_MISSING_OR_INVALID")
    identity = identity_failures(packet)
    if identity:
        # Missing rows are incomplete; contradictory/overlapping identities fail.
        gates["instrument_identity"]["status"] = "FAIL" if packet.get("instrument_intervals") else "UNRESOLVED"
        gates["instrument_identity"]["reasons"].extend(identity)
    for row in packet.get("instrument_intervals", []):
        if any(evidence.get(ref, {}).get("status") != "PASS" for ref in row.get("evidence_ids", [])):
            gates["instrument_identity"]["status"] = combine([gates["instrument_identity"]["status"], "UNRESOLVED"])
    historical_ready = all(gates[k]["status"] == "PASS" for k in HISTORICAL)
    prospective_ready = historical_ready and gates["prospective_readiness"]["status"] == "PASS"
    return {"version": VERSION, "packet_sha256": digest(canonical(packet)), "scope_sha256": scope_sha,
            "gate_code_sha256": digest(Path(__file__).read_bytes()),
            "gates": gates, "historical_recommendation": "RUN_50_HISTORICAL_AUDIT" if historical_ready else "BLOCK_HISTORICAL_AUDIT",
            "prospective_recommendation": "PROSPECTIVE_ACTIONABILITY_READY_FOR_REVIEW" if prospective_ready else "PROSPECTIVE_ACTIONABILITY_BLOCKED",
            "historical_does_not_require_live_sip": True, "audit_executed": False,
            "review_semantics": "Evidence-linked reviews are assertions; hashes establish identity, not factual/legal truth.",
            "unresolved_or_failed_evidence": {k: {"status": v["status"], "reason": v["reason"]}
                                              for k, v in evidence.items() if v["status"] != "PASS"}}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packet", default="config/dated_source_packet.json")
    parser.add_argument("--root", default=".", help="Root beneath which packet evidence paths resolve")
    parser.add_argument("--store", required=True)
    args = parser.parse_args(argv)
    store = EvidenceStore(args.store)
    run_id = uuid.uuid4().hex
    try:
        raw = Path(args.packet).read_bytes()
        packet_record = store.append("dated_source_packet", run_id, {"version": VERSION}, raw)
        result = evaluate_packet(strict_json(raw), args.root)
        result.update(packet_record_id=packet_record["id"], evaluated_at=utc_now())
    except (AuditFailure, OSError, KeyError, TypeError, ValueError) as exc:
        result = {"version": VERSION, "historical_recommendation": "BLOCK_HISTORICAL_AUDIT",
                  "prospective_recommendation": "PROSPECTIVE_ACTIONABILITY_BLOCKED",
                  "failure": str(exc) if isinstance(exc, AuditFailure) else "MISSING_OR_MALFORMED_PACKET",
                  "audit_executed": False}
    store.append("dated_source_gate_result", run_id, result)
    store.verify()
    path = Path(args.store) / ("dated_source_gate_" + run_id + ".json")
    with path.open("x", encoding="utf-8") as handle:
        json.dump(result, handle, indent=2, allow_nan=False)
    store.close()
    print(json.dumps(result, indent=2))
    return 0 if result["historical_recommendation"] == "RUN_50_HISTORICAL_AUDIT" else 2


if __name__ == "__main__":
    raise SystemExit(main())
