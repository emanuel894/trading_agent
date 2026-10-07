"""Synthetic-only Amendment 004 protocol regressions; no issuer screening."""
import copy
import hashlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

from agent import acquisition_registration as audit
from agent import cohort_selector_v3 as economic
from agent.audit_store import AuditFailure


ROOT = Path(__file__).resolve().parents[1]


class AcquisitionRegistrationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.raw = audit.REGISTRATION_PATH.read_bytes()
        cls.reg = audit.registration(cls.raw)
        # Deliberately synthetic identifiers. Never read the actual CIK inventory.
        cls.ciks = [f"{9000000000 + n:010d}" for n in range(1, 28)]

    def row(self, rank=0, status="ELIGIBLE", ciks=None):
        priority = audit.priority_order(ciks or self.ciks, self.raw)[rank]
        reason = {"ELIGIBLE": "ALL_REGISTERED_REQUIREMENTS_SOURCE_REVIEWED",
                  "INELIGIBLE": "PROVEN_NO_QUALIFYING_CLASS",
                  "UNRESOLVED": "UNRESOLVED", "FAIL": "FAIL"}[status]
        return {**priority, "registration_sha256": audit.REGISTRATION_SHA,
                "eligibility_status": status, "reason_code": reason,
                "exact_reason_or_unresolved_field": "Synthetic dated common-class review",
                "evidence_references": ([] if status == "UNRESOLVED" else
                    [{"record_id": "synthetic-review", "sha256": "a" * 64}])}

    def test_priority_deterministic_and_exact_encoding(self):
        first = audit.priority_order(self.ciks, self.raw)
        self.assertEqual(first, audit.priority_order(list(reversed(self.ciks)), self.raw))
        seed = b"ADR001-ACQUISITION-004/calendar-2025/issuer-priority/v1"
        expected = sorted((hashlib.sha256(b"adr001-acquisition-cik-priority-v1\x00"
                            + seed + b"\x00" + cik.encode("ascii")).hexdigest(), cik)
                          for cik in self.ciks)
        self.assertEqual([(r["priority_sha256"], r["cik"]) for r in first], expected)
        self.assertNotEqual([r["cik"] for r in first], sorted(self.ciks))
        self.assertEqual([r["priority"] for r in first], list(range(1, 28)))

    def test_seed_hash_encoding_domain_or_version_change_invalidates_registration(self):
        mutations = [("priority", "seed", "different-seed"),
                     ("priority", "hash_algorithm", "SHA-512"),
                     ("priority", "domain", "different-domain"),
                     ("priority", "message_encoding", "UTF-16"),
                     (None, "version", "adr001-acquisition-frame-v2")]
        for section, key, value in mutations:
            with self.subTest(key=key):
                changed = copy.deepcopy(self.reg)
                (changed[section] if section else changed)[key] = value
                with self.assertRaisesRegex(AuditFailure, "REGISTRATION_CHANGED"):
                    audit.priority_order(self.ciks, json.dumps(changed).encode())

    def test_old_ledger_registration_cannot_be_reused(self):
        row = self.row()
        row["registration_sha256"] = "0" * 64
        with self.assertRaisesRegex(AuditFailure, "LEDGER_REGISTRATION_CHANGED"):
            audit.check_ledger_prefix(self.ciks, [row], self.raw)

    def test_unresolved_first_candidate_blocks_and_cannot_be_skipped(self):
        unresolved = self.row(status="UNRESOLVED")
        result = audit.check_ledger_prefix(self.ciks, [unresolved], self.raw)
        self.assertEqual(result["status"], "BLOCKED")
        self.assertEqual(result["cik"], unresolved["cik"])
        self.assertEqual(result["eligible_claims_in_prefix"], 0)
        with self.assertRaisesRegex(AuditFailure, "CONTINUES_AFTER_BLOCK"):
            audit.check_ledger_prefix(self.ciks, [unresolved, self.row(1)], self.raw)
        with self.assertRaisesRegex(AuditFailure, "NOT_FROZEN_PRIORITY_PREFIX"):
            audit.check_ledger_prefix(self.ciks, [self.row(1)], self.raw)

    def test_missing_or_conflicting_candidate_blocks(self):
        for ledger in ([], [self.row(status="FAIL")]):
            result = audit.check_ledger_prefix(self.ciks, ledger, self.raw)
            self.assertEqual(result["status"], "BLOCKED")
            self.assertEqual(result["priority"], 1)

    def test_proved_ineligible_may_be_passed_with_evidence_receipt(self):
        ledger = [self.row(status="INELIGIBLE"), self.row(1)]
        result = audit.check_ledger_prefix(self.ciks, ledger, self.raw)
        self.assertEqual(result["priority"], 3)
        self.assertEqual(result["eligible_claims_in_prefix"], 1)
        self.assertFalse(result["source_evidence_validated"])
        ledger[0]["evidence_references"] = []
        with self.assertRaisesRegex(AuditFailure, "REQUIRES_EVIDENCE"):
            audit.check_ledger_prefix(self.ciks, ledger, self.raw)

    def test_acquisition_success_is_not_a_selection_input(self):
        for value in (True, False):
            row = self.row()
            row["acquisition_success"] = value
            with self.assertRaisesRegex(AuditFailure, "FORBIDDEN_SELECTION_INPUT"):
                audit.check_ledger_prefix(self.ciks, [row], self.raw)
        for reason in ("DOWNLOAD_FAILED", "SOURCE_UNAVAILABLE", "SUCCESS_BASED_REPLACEMENT"):
            row = self.row(status="INELIGIBLE")
            row["reason_code"] = reason
            with self.assertRaisesRegex(AuditFailure, "SUCCESS_BASED_EXCLUSION"):
                audit.check_ledger_prefix(self.ciks, [row], self.raw)

    def test_no_extra_candidate_after_twenty_five(self):
        ledger = [self.row(n) for n in range(25)]
        result = audit.check_ledger_prefix(self.ciks, ledger, self.raw)
        self.assertEqual(result["status"], "PROTOCOL_COMPLETE_REQUIRES_SOURCE_VALIDATION")
        self.assertFalse(result["audit_authorized"])
        with self.assertRaisesRegex(AuditFailure, "CONTINUES_AFTER_25"):
            audit.check_ledger_prefix(self.ciks, ledger + [self.row(25)], self.raw)

    def identity(self):
        return {"cik": self.ciks[0], "instrument_id": "research:synthetic-common",
                "lineage_id": "synthetic-lineage", "share_class": "common",
                "ticker": "SYNTHETIC", "exchange": "XNYS", "security_type": "COMMON_STOCK",
                "domestic_operating": True, "fund": False, "adr": False, "shell": False,
                "valid_from": "2024-01-01T00:00:00Z", "valid_to": "2026-01-01T00:00:00Z",
                "known_at": "2024-01-01T00:00:00Z", "evidence_ids": ["synthetic"]}

    def test_parent_ticker_substitution_rejected(self):
        row = self.identity()
        row["cik"] = self.ciks[1]
        with self.assertRaisesRegex(AuditFailure, "PARENT_OR_OTHER_ISSUER"):
            audit.validate_issuer_class_binding(self.ciks[0], row, "2025-04-01T00:00:00Z", self.raw)

    def test_common_share_and_dated_binding_still_required(self):
        at = "2025-04-01T00:00:00Z"
        row = self.identity()
        self.assertTrue(audit.validate_issuer_class_binding(self.ciks[0], row, at, self.raw))
        for kind in ("DEBT", "PREFERRED", "WARRANT", "RIGHT", "UNIT", "ETF", "ADR"):
            changed = dict(row, security_type=kind)
            self.assertFalse(audit.validate_issuer_class_binding(self.ciks[0], changed, at, self.raw))
        for field in ("valid_from", "known_at"):
            with self.assertRaisesRegex(AuditFailure, "INTERVAL_UNRESOLVED"):
                audit.validate_issuer_class_binding(self.ciks[0],
                    dict(row, **{field: "2026-01-01T00:00:00Z"}), at, self.raw)

    def test_waiver_is_acquisition_only(self):
        self.assertFalse(audit.requires_global_top500(audit.PURPOSE, self.raw))
        for purpose in ("ADR_TOP_500_RESEARCH", "ALPHA", "LIVE", "", None):
            self.assertTrue(audit.requires_global_top500(purpose, self.raw))
            with self.assertRaisesRegex(AuditFailure, "OUTSIDE_REGISTERED_PURPOSE"):
                audit.check_ledger_prefix(self.ciks, [], self.raw, purpose=purpose)

    def test_economic_universe_and_amendment_003_unchanged(self):
        self.assertEqual(audit.verify_only()["status"], "REGISTRATION_VERIFIED")
        parent_raw = (ROOT / "research/cohort_selection_registration_003.json").read_bytes()
        self.assertEqual(hashlib.sha256(parent_raw).hexdigest(), economic.REGISTRATION_SHA)
        parent = json.loads(parent_raw)
        self.assertEqual(self.reg["eligibility"]["inherited_universe_contract"], parent["universe"])
        self.assertEqual(parent["universe"]["monthly_max_issuers"], 500)
        self.assertEqual(parent["universe"]["lookback_sessions"], 60)
        self.assertEqual(parent["universe"]["minimum_median_dollar_volume_usd"], "20000000")
        self.assertEqual(parent["universe"]["minimum_prior_close_usd"], "10")
        # The economic selector cannot accept the acquisition waiver registration.
        with self.assertRaises(AuditFailure):
            economic.build_scope({}, ROOT, self.raw)

    def test_frame_and_event_rule_pinned_without_constructing_real_priorities(self):
        self.assertEqual(len(self.reg["frame"]["source_indexes"]), 4)
        self.assertEqual(self.reg["frame"]["expected_original_index_pairs"], 17289)
        self.assertEqual(self.reg["frame"]["expected_distinct_ciks"], 5974)
        events = self.reg["events"]
        self.assertEqual((events["issuers"], events["filings_per_issuer"], events["filings"]), (25, 2, 50))
        self.assertEqual(events["event_order"], ["SEC acceptance UTC ascending", "accession ASCII ascending"])
        self.assertTrue(events["original_only"])
        self.assertFalse(self.reg["future_freeze"]["allowed_now"])

    def test_invalid_ciks_duplicates_and_hash_collision_fail_closed(self):
        for bad in ("1", "0000000000", " 9000000001", "９００００００００１", 9000000001):
            with self.assertRaises(AuditFailure):
                audit.priority_order([bad], self.raw)
        with self.assertRaisesRegex(AuditFailure, "DUPLICATE_CIK"):
            audit.priority_order([self.ciks[0]] * 2, self.raw)
        real_digest = audit.digest
        def collision(raw):
            return real_digest(raw) if raw == self.raw else "a" * 64
        with patch.object(audit, "digest", side_effect=collision):
            with self.assertRaisesRegex(AuditFailure, "HASH_COLLISION"):
                audit.priority_order(self.ciks, self.raw)


if __name__ == "__main__":
    unittest.main()
