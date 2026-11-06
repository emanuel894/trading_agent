"""Fixed offline readiness research: existing inputs/features -> critique -> decision.

This is an unregistered synthetic feasibility demonstration, never an alpha,
source-admission, strategy, engine or broker entry point. Review identities are
recorded attestations, not authenticated signatures or execution authority.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict
from datetime import datetime
import json
from pathlib import Path
import sys

from agent.audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json
from agent.fed_statement_offline import load_retained
from research.lean_intraday_integration_20261023 import integration


CASES = ("baseline", "future_revision", "missing_bar", "equal_clock")
HYPOTHESIS = {
    "id": "synthetic-readiness-H1-v1",
    "question": "Are required market and policy-change features ready strictly before the common cutoff in every fixed case?",
    "opportunity_ids": list(CASES),
    "criterion": "ready == opportunities == 4; missing/late cases remain in the denominator",
    "registration": "UNREGISTERED_SYNTHETIC_DEMONSTRATION_ONLY",
    "limits": "Related technical scenarios, not independent economic samples; no outcomes, alpha, source qualification or trading.",
}


def _code_bindings():
    starter = Path(__file__).resolve().parents[1]
    names = ("agent/research_workflow_offline.py", "agent/fed_statement_offline.py",
             "agent/offline_chart_gov_demo.py", "agent/audit_store.py",
             "research/lean_intraday_integration_20261023/integration.py")
    return {name: digest((starter / name).read_bytes()) for name in names}


def prepare(root, *, input_kind="synthetic", author_id="workflow-author"):
    """Record fixed H1 before evaluating existing features; refuse existing runs."""
    if input_kind not in {"synthetic", "fed-catalog"}:
        raise ValueError("Unsupported input kind; no source or synthetic fallback")
    if not isinstance(author_id, str) or not author_id.strip():
        raise ValueError("An explicit author identity is required")
    root = Path(root)
    root.mkdir(parents=True, exist_ok=False)
    store = EvidenceStore(root)
    try:
        hypothesis = store.append("research_hypothesis", HYPOTHESIS["id"],
                                  {"author_id": author_id}, canonical(HYPOTHESIS))
        observations, measurement = {}, None
        if input_kind == "synthetic":
            cases = integration.scenarios()
            if set(cases) != set(CASES):
                raise AuditFailure("FIXTURE_OPPORTUNITY_SET_CHANGED")
            source = {}
            for name in CASES:
                sessions, bars, statements = cases[name]
                source[name] = {"sessions": sessions, "bars": [asdict(x) for x in bars],
                                "statements": [asdict(x) for x in statements]}
            source = json.loads(json.dumps(source, default=lambda value: value.isoformat()))
            source = {"capture_mode": "fixture", "synthetic": True, "cases": source}
            source_record = store.append("research_input", input_kind,
                                         {"scope": "SYNTHETIC_ONLY"}, canonical(source))
            for name in CASES:
                # Reuse accepted feature and cutoff semantics; never call native_case/run.
                observations[name] = integration.decide(*cases[name])
            measurement = {"ready": sum(
                row["sma_3"] is not None and row["sma_5"] is not None
                and row["rate_change_pp"] is not None for row in observations.values()),
                "opportunities": len(CASES)}
            scope, status = "SYNTHETIC_READINESS_ONLY", "AWAITING_INDEPENDENT_CRITIQUE"
        else:
            # No scientific availability is inferred from the catalog cutoff.
            source = load_retained().snapshot(datetime.fromisoformat("2026-10-19T00:00:00+00:00"))
            source_record = store.append("research_input", input_kind,
                                         {"scope": "CATALOG_ONLY"}, canonical(source))
            scope, status = "CATALOG_ONLY", "BLOCKED_SOURCE_QUARANTINE"
        packet = {
            "schema": "offline-readiness-packet-v1", "scope": scope, "status": status,
            "author_id": author_id, "input_kind": input_kind,
            "hypothesis_sha256": hypothesis["blob_sha"],
            "input_sha256": source_record["blob_sha"], "code_sha256": _code_bindings(),
            "observations": observations, "measurement": measurement,
            "source_admission": "NOT_GRANTED", "predictive_research": "NOT_RUN",
            "critique_requirement": "Separate reviewer must inspect this exact packet; identity fields only record an attestation.",
        }
        return store.append("research_packet", HYPOTHESIS["id"],
                            {"hypothesis_record_id": hypothesis["id"],
                             "input_record_id": source_record["id"]}, canonical(packet))
    finally:
        store.close()


def _validate_critique(critique, packet, packet_hash):
    fields = {"packet_sha256", "reviewer_id", "independent", "independence_basis",
              "verdict", "findings", "rationale"}
    if not isinstance(critique, dict) or set(critique) != fields:
        raise AuditFailure("MISSING_OR_MALFORMED_CRITIQUE")
    if len(canonical(critique)) > 16_384:
        raise AuditFailure("CRITIQUE_TOO_LARGE")
    if critique["packet_sha256"] != packet_hash:
        raise AuditFailure("STALE_CRITIQUE")
    if (critique["independent"] is not True
            or critique["reviewer_id"] == packet["author_id"]):
        raise AuditFailure("INDEPENDENT_CRITIQUE_REQUIRED")
    for name in ("reviewer_id", "independence_basis", "rationale"):
        if not isinstance(critique[name], str) or not critique[name].strip():
            raise AuditFailure("MALFORMED_CRITIQUE_ATTESTATION")
    if (not isinstance(critique["verdict"], str)
            or critique["verdict"] not in {"ACCEPT_INTERPRETATION", "REQUEST_CHANGES", "REJECT_INTERPRETATION"}
            or not isinstance(critique["findings"], list)
            or len(critique["findings"]) > 20
            or any(not isinstance(x, str) or not x.strip() for x in critique["findings"])):
        raise AuditFailure("MALFORMED_CRITIQUE_VERDICT")


def finalize(root, packet_id, critique):
    """Seal one research decision after actual external critique, preserving blocks."""
    if not (Path(root) / "evidence.sqlite").is_file():
        raise AuditFailure("RESEARCH_RUN_NOT_FOUND")
    store = EvidenceStore(root)
    try:
        store.verify()
        record = store.get(packet_id)
        if record["kind"] != "research_packet":
            raise AuditFailure("RESEARCH_PACKET_REQUIRED")
        packet = strict_json(store.raw(record))
        if packet["code_sha256"] != _code_bindings():
            raise AuditFailure("IMPLEMENTATION_CHANGED_SINCE_PACKET")
        for field, kind, expected in (
            ("hypothesis_record_id", "research_hypothesis", packet["hypothesis_sha256"]),
            ("input_record_id", "research_input", packet["input_sha256"]),
        ):
            dependency = store.get(record["metadata"][field])
            if dependency["kind"] != kind or dependency["blob_sha"] != expected:
                raise AuditFailure("PACKET_DEPENDENCY_MISMATCH")
        _validate_critique(critique, packet, record["blob_sha"])
        if packet["scope"] == "CATALOG_ONLY":
            status = "BLOCKED_SOURCE_QUARANTINE"
        elif critique["verdict"] != "ACCEPT_INTERPRETATION" or critique["findings"]:
            status = "BLOCKED_CRITIQUE"
        else:
            status = ("SYNTHETIC_HYPOTHESIS_SUPPORTED" if packet["measurement"] ==
                      {"ready": 4, "opportunities": 4} else "REJECT_READINESS_HYPOTHESIS")
        result = {"schema": "offline-readiness-decision-v1", "status": status,
                  "scope": packet["scope"], "packet_sha256": record["blob_sha"],
                  "critique_sha256": digest(canonical(critique)),
                  "measurement": packet["measurement"], "source_admission": "NOT_GRANTED",
                  "predictive_research": "NOT_RUN", "critique_verdict": critique["verdict"],
                  "limits": HYPOTHESIS["limits"]}
        with store.transaction():
            if store.records("research_decision", packet_id):
                raise AuditFailure("RESEARCH_PACKET_ALREADY_DECIDED")
            reviewed = store.append_in_transaction("research_critique", packet_id,
                                                   {"packet_record_id": packet_id}, canonical(critique))
            return store.append_in_transaction("research_decision", packet_id,
                                               {"packet_record_id": packet_id,
                                                "critique_record_id": reviewed["id"]}, canonical(result))
    finally:
        store.close()


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    new = commands.add_parser("prepare")
    new.add_argument("--root", required=True)
    new.add_argument("--input", choices=("synthetic", "fed-catalog"), default="synthetic")
    new.add_argument("--author", required=True)
    finish = commands.add_parser("finalize")
    finish.add_argument("--root", required=True)
    finish.add_argument("--packet-id", required=True)
    finish.add_argument("--critique", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            record = prepare(args.root, input_kind=args.input, author_id=args.author)
        else:
            with Path(args.critique).open("rb") as handle:
                raw = handle.read(16_385)
            if len(raw) > 16_384:
                raise AuditFailure("CRITIQUE_TOO_LARGE")
            record = finalize(args.root, args.packet_id, strict_json(raw))
        print(canonical(record).decode())
        return 0
    except (AuditFailure, ValueError, OSError) as error:
        print(f"STOPPED: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
