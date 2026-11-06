"""New workflow joins and decision gates; existing feature/native oracles are reused."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent.audit_store import AuditFailure, EvidenceStore

try:
    from agent import research_workflow_offline as workflow
except ImportError:
    workflow = None


class ResearchWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(workflow, "The research packet/critique/decision join is missing")
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "run"

    def prepared(self, kind="synthetic"):
        return workflow.prepare(self.root, input_kind=kind, author_id="author:A")

    def payload(self, record):
        store = EvidenceStore(self.root)
        try:
            return json.loads(store.raw(record))
        finally:
            store.close()

    def critique(self, packet, **changes):
        # Explicit test double of an external critique; never reported as real review.
        result = {"packet_sha256": packet["blob_sha"], "reviewer_id": "test-reviewer:B",
                  "independent": True, "independence_basis": "synthetic test double only",
                  "verdict": "ACCEPT_INTERPRETATION", "findings": [],
                  "rationale": "The two unavailable cases falsify all-case readiness; no market claim."}
        result.update(changes)
        return result

    def test_prepare_preserves_four_opportunities_and_waits_for_critique(self):
        record = self.prepared()
        packet = self.payload(record)
        self.assertEqual(packet["scope"], "SYNTHETIC_READINESS_ONLY")
        self.assertEqual(packet["measurement"], {"ready": 2, "opportunities": 4})
        self.assertEqual(set(packet["observations"]),
                         {"baseline", "future_revision", "missing_bar", "equal_clock"})
        self.assertEqual(packet["status"], "AWAITING_INDEPENDENT_CRITIQUE")
        store = EvidenceStore(self.root)
        try:
            self.assertEqual(len(store.records("research_hypothesis")), 1)
            self.assertFalse(store.records("research_decision"))
            self.assertEqual(store.verify()["status"], "VERIFIED")
        finally:
            store.close()

    def test_critique_precedes_auditable_rejection_without_alpha_promotion(self):
        packet = self.prepared()
        decision = workflow.finalize(self.root, packet["id"], self.critique(packet))
        result = self.payload(decision)
        self.assertEqual(result["status"], "REJECT_READINESS_HYPOTHESIS")
        self.assertEqual(result["measurement"], {"ready": 2, "opportunities": 4})
        self.assertEqual(result["source_admission"], "NOT_GRANTED")
        self.assertEqual(result["predictive_research"], "NOT_RUN")
        store = EvidenceStore(self.root)
        try:
            records = store.records()
            self.assertEqual([x["kind"] for x in records],
                             ["research_hypothesis", "research_input", "research_packet",
                              "research_critique", "research_decision"])
            self.assertEqual(decision["metadata"]["critique_record_id"], records[3]["id"])
            self.assertEqual(result["packet_sha256"], packet["blob_sha"])
            self.assertEqual(store.verify()["records"], 5)
        finally:
            store.close()

    def test_absent_stale_same_author_or_unattested_critique_cannot_decide(self):
        packet = self.prepared()
        for critique in (None, self.critique(packet, packet_sha256="0" * 64),
                         self.critique(packet, reviewer_id="author:A"),
                         self.critique(packet, independent=False)):
            with self.subTest(critique=critique):
                with self.assertRaises((AuditFailure, ValueError)):
                    workflow.finalize(self.root, packet["id"], critique)
        store = EvidenceStore(self.root)
        try:
            self.assertFalse(store.records("research_decision"))
        finally:
            store.close()

    def test_critic_objections_block_a_recorded_measurement(self):
        packet = self.prepared()
        decision = workflow.finalize(self.root, packet["id"], self.critique(
            packet, verdict="REQUEST_CHANGES", findings=["Interpretation requires revision."]))
        self.assertEqual(self.payload(decision)["status"], "BLOCKED_CRITIQUE")

    def test_changed_implementation_cannot_finalize_an_old_reviewed_packet(self):
        packet = self.prepared()
        with patch.object(workflow, "_code_bindings", return_value={}):
            with self.assertRaises(AuditFailure):
                workflow.finalize(self.root, packet["id"], self.critique(packet))

    def test_malformed_verdict_is_rejected_as_a_critique_failure(self):
        packet = self.prepared()
        with self.assertRaises(AuditFailure):
            workflow.finalize(self.root, packet["id"], self.critique(packet, verdict=[]))

    def test_catalog_fed_cannot_be_promoted_by_approving_critique(self):
        packet_record = self.prepared("fed-catalog")
        packet = self.payload(packet_record)
        self.assertEqual(packet["status"], "BLOCKED_SOURCE_QUARANTINE")
        self.assertEqual(packet["observations"], {})
        self.assertIsNone(packet["measurement"])
        self.assertEqual(packet["scope"], "CATALOG_ONLY")
        result = self.payload(workflow.finalize(
            self.root, packet_record["id"], self.critique(packet_record)))
        self.assertEqual(result["status"], "BLOCKED_SOURCE_QUARANTINE")
        self.assertEqual(result["source_admission"], "NOT_GRANTED")

    def test_repeat_prepare_and_finalize_preserve_existing_run(self):
        packet = self.prepared()
        with self.assertRaises(FileExistsError):
            self.prepared()
        first = workflow.finalize(self.root, packet["id"], self.critique(packet))
        with self.assertRaises(AuditFailure):
            workflow.finalize(self.root, packet["id"], self.critique(packet))
        store = EvidenceStore(self.root)
        try:
            self.assertEqual(store.records("research_decision"), [first])
            self.assertEqual(store.verify()["records"], 5)
        finally:
            store.close()

    def test_packet_bytes_repeat_without_reusing_random_audit_record_ids(self):
        first = self.prepared()
        second = workflow.prepare(Path(self.temporary.name) / "second", author_id="author:A")
        self.assertEqual(first["blob_sha"], second["blob_sha"])
        self.assertNotEqual(first["id"], second["id"])

    def test_changed_packet_bytes_fail_before_critique_or_decision(self):
        packet = self.prepared()
        (self.root / "objects" / packet["blob_sha"]).write_bytes(b"{}")
        with self.assertRaises(AuditFailure):
            workflow.finalize(self.root, packet["id"], self.critique(packet))

    def test_wrong_input_kind_never_falls_back_to_synthetic(self):
        with self.assertRaises(ValueError):
            self.prepared("real-market")
        self.assertFalse(self.root.exists())


if __name__ == "__main__":
    unittest.main()
