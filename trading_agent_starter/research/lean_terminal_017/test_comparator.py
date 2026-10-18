"""Adversarial checks of acceptance; frozen observed records are never mutated on disk."""
import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("terminal_comparator", ROOT / "compare.py")
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


class ComparatorAcceptanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.unknown = json.loads((ROOT / "evidence/Q01_user_defined_unknown.attempt07.json").read_text())
        cls.expected = json.loads((ROOT / "fixtures_v2/Q01_user_defined_unknown.expected.json").read_text())
        cls.known = json.loads((ROOT / "evidence/Q02_user_defined_known.attempt11.json").read_text())
        cls.known_expected = json.loads((ROOT / "fixtures_v2/Q02_user_defined_known.expected.json").read_text())

    def rejects(self, change, *, blocker=None, known=False):
        actual = copy.deepcopy(self.known if known else self.unknown)
        change(actual)
        with self.assertRaises(gate.GateMismatch) as caught:
            gate.assess(actual, self.known_expected if known else self.expected)
        if blocker is not None:
            self.assertEqual(blocker, caught.exception.blocker)

    def test_unchanged_observed_case_passes(self):
        self.assertEqual("PASS", gate.assess(self.unknown, self.expected))

    def test_vanished_engine_holding_blocks(self):
        self.rejects(lambda x: x["snapshots"][2].update(engine_quantity="0"), blocker=True)

    def test_removed_engine_security_blocks(self):
        self.rejects(lambda x: x["snapshots"][3].update(engine_security_present=False), blocker=True)

    def test_invented_cash_blocks(self):
        self.rejects(lambda x: x["snapshots"][2].update(cash="9375"), blocker=True)

    def test_changed_denominator_blocks(self):
        self.rejects(lambda x: x["snapshots"][2].update(denominator=0), blocker=True)

    def test_late_lifecycle_timestamp_is_rejected(self):
        self.rejects(lambda x: x["events"][3].update(utc="2025-01-06T15:00:01.0000000Z"))

    def test_class_substitution_is_rejected(self):
        self.rejects(lambda x: x["external_identity"].update(class_id="B"))

    def test_nav_probe_cannot_call_destination(self):
        self.rejects(lambda x: x["admission_probes"][0].update(submission_delegate_called=True))

    def test_cancel_request_cannot_release_reservation(self):
        self.rejects(lambda x: x["reservation_observations"][2].update(reserved_cash="0"))

    def test_missing_native_order_is_rejected(self):
        self.rejects(lambda x: x["native_order_events"].pop())

    def test_sparse_cleanup_or_end_evidence_is_rejected(self):
        self.rejects(lambda x: x["snapshots"].pop())

    def test_duplicate_settlement_mutation_blocks(self):
        self.rejects(lambda x: x["snapshots"][5].update(action_settlements=2), known=True, blocker=True)


if __name__ == "__main__":
    unittest.main(verbosity=2)
