"""Amendment 005: isolated, offline acquisition structural-time validation.

No economic-selector override, candidate admission, network or ledger mutation.
Grounded review spans are reviewed assertions, not automated proof of truth.
"""
from datetime import date
from pathlib import Path

from .acquisition_registration import PURPOSE, verify_only
from .audit_store import AuditFailure, digest, strict_json, timestamp

ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_PATH = ROOT / "research/structural_identity_registration_005.json"
REGISTRATION_SHA = "26eeca3bc843f0de0dab53b61fa2008773e1616d888bb165111fabe8a2c38cc5"
CLOCK_KEYS = {"published_at", "captured_at", "revised_at", "known_at", "available_at"}


def registration(raw=None, root=ROOT):
    raw = REGISTRATION_PATH.read_bytes() if raw is None else raw
    if digest(raw) != REGISTRATION_SHA:
        raise AuditFailure("STRUCTURAL_REGISTRATION_CHANGED")
    reg = strict_json(raw)
    verify_only(root)
    for name, expected in reg["protected_sha256"].items():
        if digest((root / name).read_bytes()) != expected:
            raise AuditFailure("STRUCTURAL_PROTECTED_ARTIFACT_CHANGED")
    return reg


def grounded(ref, store):
    if not isinstance(ref, dict) or set(ref) != {"record_id", "sha256", "span"}:
        raise AuditFailure("GROUNDED_REFERENCE_UNRESOLVED")
    record = store.get(ref["record_id"])
    raw = store.raw(record)
    if digest(raw) != ref["sha256"]:
        raise AuditFailure("REFERENCE_HASH_CONFLICT")
    if (not isinstance(ref["span"], str) or not ref["span"].strip()
            or ref["span"].encode("utf-8") not in raw):
        raise AuditFailure("SOURCE_SPAN_UNRESOLVED")
    return record


def clocks(evidence, store):
    record = grounded(evidence["source_record"], store)
    times = evidence["source_times"]
    if not isinstance(times, dict) or set(times) != CLOCK_KEYS:
        raise AuditFailure("SOURCE_CLOCKS_UNRESOLVED")
    # Preserve supplied revision/publication metadata; never synthesize clocks.
    if (times != record["metadata"].get("source_times")
            or evidence["retrieved_at"] != record["metadata"].get("retrieved_at")):
        raise AuditFailure("SOURCE_CLOCK_PROVENANCE_CONFLICT")
    timestamp(evidence["retrieved_at"])
    for value in times.values():
        if value is not None:
            timestamp(value)
    return times


def _structural(evidence, requirement, store, reg, corroboration=None):
    if evidence["field"] not in reg["structural_fields"]:
        raise AuditFailure("OUTSIDE_STRUCTURAL_EXCEPTION")
    if (evidence["cik"] != requirement["cik"]
            or evidence["research_id"] != requirement["research_id"]
            or evidence["field"] != requirement["field"]):
        raise AuditFailure("ISSUER_CLASS_BINDING_CONFLICT")
    clocks(evidence, store)  # No knowledge-time cutoff for this narrow exception.
    semantics = evidence["semantics"]
    if (semantics["kind"] not in reg["admissible_semantics"]
            or evidence["field"] not in semantics["field_scope"]):
        raise AuditFailure("HISTORICAL_VALID_STATE_SEMANTICS_UNRESOLVED")
    documented = grounded(semantics["documentation"], store)["metadata"]
    source = grounded(evidence["source_record"], store)["metadata"]
    # Bind claims to preserved, reviewed source semantics, not caller labels.
    # These metadata are source-review assertions and need grounded review;
    # the raw probe deliberately does not generate them or admit evidence.
    if (documented.get("historical_state_semantics") != semantics["kind"]
            or evidence["field"] not in documented.get("field_scope", [])
            or source.get("historical_state_semantics") != semantics["kind"]):
        raise AuditFailure("HISTORICAL_VALID_STATE_SEMANTICS_UNRESOLVED")
    grounded(evidence["review_record"], store)
    if not evidence["reviewer"] or not evidence["rationale"]:
        raise AuditFailure("SOURCE_REVIEW_UNRESOLVED")
    if (evidence["lineage_complete"] is not True
            or evidence["class_set_complete"] is not True):
        raise AuditFailure("LINEAGE_OR_CLASS_COMPLETENESS_UNRESOLVED")
    if evidence["transitions_resolved"] is not True:
        raise AuditFailure("BOUNDARY_CARRY_IN_OR_TRANSITION_UNRESOLVED")
    valid = evidence["valid_time"]
    if (source.get("valid_time") != valid
            or documented.get("resolution") != valid["resolution"]):
        raise AuditFailure("SOURCE_RESOLUTION_UNRESOLVED")
    if valid["resolution"] == "date":
        day = date.fromisoformat(valid["date"])
        if requirement["resolution"] == "date":
            if day != date.fromisoformat(requirement["date"]):
                raise AuditFailure("HISTORICAL_DATE_UNRESOLVED")
        elif requirement["resolution"] == "instant":
            if corroboration is None:
                raise AuditFailure("EXACT_INSTANT_CORROBORATION_UNRESOLVED")
            if (corroboration["source_record"]["sha256"] == evidence["source_record"]["sha256"]
                    or corroboration["valid_time"]["resolution"] != "interval"
                    or corroboration["value"] != evidence["value"]):
                raise AuditFailure("INDEPENDENT_CORROBORATION_UNRESOLVED")
            _structural(corroboration, requirement, store, reg)
        else:
            raise AuditFailure("REQUIRED_RESOLUTION_UNRESOLVED")
    elif valid["resolution"] == "interval":
        # An interval is an explicitly reviewed exact-time claim, never an
        # automatic conversion of a provider's calendar date to midnight.
        if requirement["resolution"] != "instant":
            raise AuditFailure("REQUIRED_RESOLUTION_UNRESOLVED")
        start, end, at = (timestamp(valid["from"]), timestamp(valid["to"]),
                          timestamp(requirement["at"]))
        grounded(valid["interval_evidence"], store)
        if not start <= at < end:
            raise AuditFailure("HISTORICAL_INTERVAL_UNRESOLVED")
    else:
        raise AuditFailure("SOURCE_RESOLUTION_UNRESOLVED")


def validate_structural(evidence, requirement, store, *, purpose, corroboration=None):
    reg = registration()
    if purpose != PURPOSE:
        raise AuditFailure("ACQUISITION_EXCEPTION_OUTSIDE_PURPOSE")
    try:
        _structural(evidence, requirement, store, reg, corroboration)
        return {"status": "PASS", "scope": "STRUCTURAL_VALID_STATE_ONLY",
                "registration_sha256": REGISTRATION_SHA, "eligibility_decision": None}
    except AuditFailure as exc:
        return {"status": "FAIL" if "CONFLICT" in str(exc) else "UNRESOLVED",
                "reason": str(exc), "eligibility_decision": None}
    except (KeyError, TypeError, ValueError):
        return {"status": "UNRESOLVED", "reason": "STRUCTURAL_INPUT_MALFORMED",
                "eligibility_decision": None}


def validate_decision_time(evidence, at, store):
    """Explicit no-exception guard; existing pipeline guards remain unchanged."""
    reg = registration()
    if evidence.get("field") not in reg["excluded_fields"]:
        raise AuditFailure("DECISION_EVIDENCE_FIELD_UNREGISTERED")
    try:
        times = clocks(evidence, store)
        if any(times[k] is None or timestamp(times[k]) > timestamp(at)
               for k in ("known_at", "available_at")):
            raise AuditFailure("DECISION_TIME_AVAILABILITY_UNRESOLVED")
        return {"status": "PASS", "scope": "DECISION_TIME_AVAILABILITY"}
    except AuditFailure as exc:
        return {"status": "UNRESOLVED", "reason": str(exc)}
    except (KeyError, TypeError, ValueError):
        return {"status": "UNRESOLVED", "reason": "DECISION_EVIDENCE_MALFORMED"}
