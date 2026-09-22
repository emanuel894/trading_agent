"""Failure-oriented mini-gate checks; fixtures are not market measurements."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent.access_fastpath import (comparator_diagnostics, load_snapshot, main,
                                   prepare_snapshot, source_documents)
from agent.audit_market import SIPSource
from agent.audit_store import AuditFailure, EvidenceStore, canonical, utc_now
from test_evidence_audit import FixtureHTTP, html, quote


class FastPathTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        self.source = EvidenceStore(self.root / "source")
        self.dest = EvidenceStore(self.root / "dest")

    def tearDown(self):
        self.source.close()
        self.dest.close()
        self.tmp.cleanup()

    def doc(self, year, report_date, accepted, raw=None):
        return self.source.append("document", str(year), {
            "source": "SEC", "acceptance_crosschecked": True, "cik": "0000320193",
            "primary": True, "form": "10-Q", "accession": str(year),
            "report_date": report_date, "accepted_at": accepted,
            "first_observed_at": utc_now(), "ingestion_complete_at": utc_now(),
            "original_public_version_guaranteed": False}, raw or html(year))

    def snapshot(self):
        self.doc(2023, "2023-03-31", "2023-05-15T13:00:00Z")
        self.doc(2024, "2024-03-31", "2024-05-15T13:00:00Z")
        return prepare_snapshot(self.source, self.dest, source_documents(self.source),
                                "0000320193", "2024-05-15T13:00:00Z", self.source.verify()["head_hash"])

    def test_preindex_excludes_current_and_future_without_network(self):
        snap = self.snapshot()
        with patch("agent.audit_http.ReadOnlyHTTP.get", side_effect=AssertionError("network forbidden")):
            entries = load_snapshot(self.dest, snap, "2024-05-15T13:00:00Z")
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["parsed"]["fiscal"]["DocumentFiscalYearFocus"], "2023")
        self.assertFalse(entries[0]["parsed"]["document"]["metadata"]["original_public_version_guaranteed"])

    def test_backfill_is_not_prospective_and_later_cutoff_not_reusable_earlier(self):
        snap = self.snapshot()
        with self.assertRaisesRegex(AuditFailure, "NOT_PREPARED_BEFORE_EVENT"):
            load_snapshot(self.dest, snap, "2024-05-15T13:00:00Z", prospective=True)
        with self.assertRaisesRegex(AuditFailure, "INCLUDES_FUTURE_KNOWLEDGE"):
            load_snapshot(self.dest, snap, "2023-05-15T13:00:00Z")

    def test_tampering_or_parser_change_rejects_warm_evidence(self):
        snap = self.snapshot()
        with patch("agent.access_fastpath.PARSER_VERSION", "different"):
            with self.assertRaisesRegex(AuditFailure, "PARSER_VERSION_MISMATCH"):
                load_snapshot(self.dest, snap, "2024-05-15T13:00:00Z")
        entries = load_snapshot(self.dest, snap, "2024-05-15T13:00:00Z")
        sha = entries[0]["parsed"]["document"]["blob_sha"]
        (self.dest.objects / sha).write_bytes(b"tampered")
        with self.assertRaisesRegex(AuditFailure, "BLOB_HASH_MISMATCH"):
            load_snapshot(self.dest, snap, "2024-05-15T13:00:00Z")

    def test_conflicting_historical_versions_never_choose_latest(self):
        self.doc(2023, "2023-03-31", "2023-05-15T13:00:00Z")
        self.doc(2023, "2023-03-31", "2023-05-15T13:00:00Z", html(2023) + b"different")
        with self.assertRaisesRegex(AuditFailure, "CONFLICTING_CAPTURED_DOCUMENT_VERSION"):
            source_documents(self.source)

    def test_fiscal_diagnostic_measures_week_years_and_an_outside_window(self):
        # Synthetic structural coverage, never reported as empirical false abstentions.
        first = datetime(2021, 3, 31, tzinfo=timezone.utc)
        for year, offset in [(2021, 0), (2022, 364), (2023, 364 + 371), (2024, 364 + 371 + 390)]:
            report = first + timedelta(days=offset)
            self.doc(year, report.date().isoformat(), (report + timedelta(days=30)).isoformat())
        diag = comparator_diagnostics(self.source, self.dest, source_documents(self.source),
                                      self.source.verify()["head_hash"])
        self.assertEqual([p["day_distance"] for p in diag["pairs"]], [364, 371, 390])
        self.assertEqual(diag["supported_pairs"], 3)
        self.assertEqual(diag["false_abstentions"], 1)
        self.assertFalse(diag["production_comparator_changed"])

    def test_missing_input_still_persists_blocked_report(self):
        with patch("builtins.print"):
            code = main(["--source-store", str(self.root / "missing"), "--store", str(self.root / "gate"),
                         "--account-observation", str(self.root / "missing.json")])
        self.assertEqual(code, 2)
        store = EvidenceStore(self.root / "gate")
        try:
            result = store.records("access_fastpath_report")[0]["metadata"]
            self.assertEqual(result["recommendation"], "BLOCK_HISTORICAL_AUDIT")
            self.assertTrue(result["failures"])
            self.assertEqual(store.verify()["status"], "VERIFIED")
        finally:
            store.close()

    def test_future_market_requests_are_separate_and_cannot_change_sealed_result(self):
        calendar = [{"date": d, "open": "09:30", "close": "16:00"} for d in ("2024-05-14", "2024-05-15")]
        times = [datetime(2024, 5, 14, 19, 59, tzinfo=timezone.utc)] + [
            datetime(2024, 5, 15, 13, 30, tzinfo=timezone.utc) + timedelta(minutes=i) for i in range(5)]
        bars = [dict(t=t.isoformat(), o=100, h=101, l=99, c=100, v=1000) for t in times]
        q = quote("2024-05-15T13:34:59.999999999Z")
        http = FixtureHTTP(self.dest, [calendar, {"bars": {"AAPL": bars, "SPY": bars}},
                                       {"quotes": {"AAPL": [q], "SPY": [q]}}])
        market = SIPSource(self.dest, http)
        context = market.context("AAPL", "2024-05-15T13:10:00Z")
        self.assertEqual(context["failures"], [])
        saved = self.dest.append("audit_result", "test", {"status": "ELIGIBLE", "market": context})
        before = canonical(saved)
        with patch.object(market, "pages", side_effect=AuditFailure("HTTP_403")):
            quality = market.post_decision_context(saved)
        self.assertFalse(quality["metadata"]["affects_admission"])
        self.assertEqual(quality["metadata"]["failures"], ["bars:HTTP_403", "quotes:HTTP_403"])
        self.assertEqual(before, canonical(self.dest.get(saved["id"])))
        self.assertEqual(self.dest.verify()["status"], "VERIFIED")


if __name__ == "__main__":
    unittest.main()
