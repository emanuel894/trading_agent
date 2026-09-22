"""Amendment 004 offline registration and candidate-ledger protocol.

No source acquisition, eligibility screening, cohort construction or audit CLI.
Ledger checks validate protocol, NOT the truth/completeness of linked evidence.
Only synthetic candidate inputs are exercised in this registration milestone.
"""
from pathlib import Path
import re

from .audit_store import AuditFailure, digest, strict_json, timestamp
from .cohort_selector import structurally_eligible

REGISTRATION_SHA = "c4dfc00f202ef93a3b87cfb8928f75c4a7e152db6a3253260187bdb9b0173409"
PURPOSE = "ACQUISITION_PROVENANCE_FEASIBILITY_ONLY"
ROOT = Path(__file__).resolve().parents[1]
REGISTRATION_PATH = ROOT / "research/acquisition_frame_registration_004.json"


def registration(raw):
    if digest(raw) != REGISTRATION_SHA:
        raise AuditFailure("ACQUISITION_REGISTRATION_CHANGED")
    return strict_json(raw)


def requires_global_top500(purpose, raw):
    """The waiver cannot change the economic selector's contract."""
    registration(raw)
    return purpose != PURPOSE


def cik10(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9]{10}", value) or int(value) == 0:
        raise AuditFailure("CIK_MUST_BE_POSITIVE_TEN_ASCII_DIGITS")
    return value


def priority_order(ciks, raw):
    """Pure protocol helper; caller must separately prove complete frame binding."""
    rule = registration(raw)["priority"]
    if not isinstance(ciks, (list, tuple)) or not ciks:
        raise AuditFailure("EMPTY_OR_INVALID_CIK_FRAME")
    values = [cik10(cik) for cik in ciks]
    if len(set(values)) != len(values):
        raise AuditFailure("DUPLICATE_CIK_IN_PRIORITY_FRAME")
    prefix = rule["domain"].encode("ascii") + b"\0" + rule["seed"].encode("utf-8") + b"\0"
    pairs = [(digest(prefix + cik.encode("ascii")), cik) for cik in values]
    if len({key for key, _ in pairs}) != len(pairs):
        raise AuditFailure("PRIORITY_HASH_COLLISION")
    return [{"priority": n, "priority_sha256": key, "cik": cik}
            for n, (key, cik) in enumerate(sorted(pairs), 1)]


def validate_issuer_class_binding(cik, identity, at, raw):
    """Dated structural guard, not a replacement for source/lineage review."""
    registration(raw)
    cik10(cik)
    if identity.get("cik") != cik:
        raise AuditFailure("PARENT_OR_OTHER_ISSUER_TICKER_SUBSTITUTION")
    if (not isinstance(identity.get("instrument_id"), str)
            or not identity["instrument_id"].startswith("research:")
            or not identity.get("lineage_id") or not identity.get("share_class")
            or not identity.get("ticker") or not identity.get("evidence_ids")):
        raise AuditFailure("CLASS_LINEAGE_EVIDENCE_UNRESOLVED")
    instant = timestamp(at)
    if not all(identity.get(k) for k in ("valid_from", "valid_to", "known_at")):
        raise AuditFailure("DATED_CLASS_INTERVAL_UNRESOLVED")
    if (not (timestamp(identity["valid_from"]) <= instant < timestamp(identity["valid_to"]))
            or timestamp(identity["known_at"]) > instant):
        raise AuditFailure("DATED_CLASS_INTERVAL_UNRESOLVED")
    for field in ("security_type", "exchange", "domestic_operating", "shell", "fund", "adr"):
        if field not in identity:
            raise AuditFailure("CLASS_CLASSIFICATION_UNRESOLVED")
    return structurally_eligible(identity, at)


def _evidence_references(refs):
    if not isinstance(refs, list):
        raise AuditFailure("INVALID_LEDGER_EVIDENCE_REFERENCES")
    for ref in refs:
        if (not isinstance(ref, dict) or set(ref) != {"record_id", "sha256"}
                or not isinstance(ref["record_id"], str) or not ref["record_id"].strip()
                or not isinstance(ref["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", ref["sha256"])):
            raise AuditFailure("INVALID_LEDGER_EVIDENCE_REFERENCES")


def check_ledger_prefix(ciks, ledger, raw, *, purpose=PURPOSE):
    """Check a reviewed ledger prefix, without selecting events or authorizing work.

Presence of an evidence reference is deliberately not called proof. A future
source reviewer must verify its bytes, grounding and scope before acting on it.
This function cannot emit RUN_50_HISTORICAL_AUDIT or a frozen manifest.
"""
    reg = registration(raw)
    if requires_global_top500(purpose, raw):
        raise AuditFailure("ACQUISITION_WAIVER_OUTSIDE_REGISTERED_PURPOSE")
    order = priority_order(ciks, raw)
    if not isinstance(ledger, list) or len(ledger) > len(order):
        raise AuditFailure("INVALID_LEDGER_LENGTH")
    eligible_count = 0
    for index, expected in enumerate(order):
        if index == len(ledger):
            return {"status": "BLOCKED", "reason": "UNRESOLVED_CANDIDATE",
                    **expected, "eligible_claims_in_prefix": eligible_count,
                    "source_evidence_validated": False}
        row = ledger[index]
        if not isinstance(row, dict) or set(row) != set(reg["ledger"]["fields"]):
            raise AuditFailure("INVALID_LEDGER_FIELDS_OR_FORBIDDEN_SELECTION_INPUT")
        if row["registration_sha256"] != REGISTRATION_SHA:
            raise AuditFailure("LEDGER_REGISTRATION_CHANGED")
        if (type(row["priority"]) is not int
                or any(row[key] != expected[key] for key in expected)):
            raise AuditFailure("LEDGER_NOT_FROZEN_PRIORITY_PREFIX")
        status = row["eligibility_status"]
        if status not in reg["ledger"]["statuses"]:
            raise AuditFailure("INVALID_ELIGIBILITY_STATUS")
        if (not isinstance(row["exact_reason_or_unresolved_field"], str)
                or not row["exact_reason_or_unresolved_field"].strip()):
            raise AuditFailure("EXACT_LEDGER_REASON_REQUIRED")
        _evidence_references(row["evidence_references"])
        if status in {"UNRESOLVED", "FAIL"}:
            if row["reason_code"] != status:
                raise AuditFailure("INVALID_LEDGER_REASON_CODE")
            if len(ledger) != index + 1:
                raise AuditFailure("LEDGER_CONTINUES_AFTER_BLOCK")
            return {"status": "BLOCKED", "reason": status, **expected,
                    "field": row["exact_reason_or_unresolved_field"],
                    "eligible_claims_in_prefix": eligible_count,
                    "source_evidence_validated": False}
        if not row["evidence_references"]:
            raise AuditFailure("DECISIVE_LEDGER_ENTRY_REQUIRES_EVIDENCE")
        if status == "INELIGIBLE":
            if row["reason_code"] not in reg["ledger"]["ineligible_reason_codes"]:
                raise AuditFailure("UNPROVEN_OR_SUCCESS_BASED_EXCLUSION")
        else:
            if row["reason_code"] != "ALL_REGISTERED_REQUIREMENTS_SOURCE_REVIEWED":
                raise AuditFailure("INVALID_ELIGIBLE_REASON_CODE")
            eligible_count += 1
        if eligible_count == reg["events"]["issuers"]:
            if len(ledger) != index + 1:
                raise AuditFailure("LEDGER_CONTINUES_AFTER_25_ISSUERS")
            return {"status": "PROTOCOL_COMPLETE_REQUIRES_SOURCE_VALIDATION",
                    "eligible_claims_in_prefix": eligible_count,
                    "source_evidence_validated": False, "audit_authorized": False}
    return {"status": "BLOCKED", "reason": "INSUFFICIENT_ELIGIBLE_ISSUERS",
            "eligible_claims_in_prefix": eligible_count, "source_evidence_validated": False}


def verify_only(root=ROOT):
    raw = (root / "research/acquisition_frame_registration_004.json").read_bytes()
    reg = registration(raw)
    for name, expected in reg["protected_artifacts_sha256"].items():
        if digest((root / name).read_bytes()) != expected:
            raise AuditFailure("PROTECTED_PRIOR_ARTIFACT_CHANGED")
    return {"status": "REGISTRATION_VERIFIED", "registration_sha256": digest(raw),
            "real_candidates_screened": 0, "cohort_constructed": False}


def main():
    import argparse
    import json
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(verify_only(), sort_keys=True))


if __name__ == "__main__":
    main()
