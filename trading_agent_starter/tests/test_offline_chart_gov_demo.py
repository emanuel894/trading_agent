"""Synthetic-only numerical and clock oracles for Issue #34.

These fail if a future revision is selected, a gap is filled, a current high
enters the breakout baseline, or source/processing clocks are conflated.
"""
from dataclasses import replace
from datetime import timedelta
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from agent import offline_chart_gov_demo as demo


class ChartTests(unittest.TestCase):
    def setUp(self):
        self.sessions, self.bars = demo.chart_fixture()
        self.cutoff = self.sessions[5] + timedelta(seconds=10)

    def table(self, bars=None, cutoff=None):
        return demo.chart_snapshot(self.sessions, self.bars if bars is None else bars,
                                   self.cutoff if cutoff is None else cutoff)

    def test_hand_computable_features(self):
        rows = self.table()["rows"]
        self.assertEqual([r["close"] for r in rows], [100, 100, 100, 102, 104, 108])
        row = rows[5]
        self.assertAlmostEqual(row["sma_3"], 314 / 3)
        self.assertAlmostEqual(row["sma_5"], 514 / 5)
        changes = [2 / 100, 2 / 102, 4 / 104]
        mean = sum(changes) / 3
        expected = math.sqrt(sum((v - mean) ** 2 for v in changes) / 3)
        self.assertAlmostEqual(row["volatility_3"], expected)
        self.assertEqual(row["range_3"], 8)
        self.assertEqual(row["breakout_distance_3"], 3)
        self.assertEqual(row["breakout"], "above_prior_high")
        self.assertEqual(row["volume_change"], 2)
        self.assertEqual(row["volume_ratio_3"], 3)
        self.assertEqual(rows[2]["sma_3"], 100)
        self.assertIsNone(rows[2]["volatility_3"])
        self.assertIsNone(rows[0]["sma_3"])

    def test_each_required_clock_is_strictly_before_cutoff(self):
        original = self.bars[0]
        boundary = original.clocks.verified
        self.assertIsNone(self.table(cutoff=boundary)["rows"][0]["close"])
        self.assertEqual(self.table(cutoff=boundary + timedelta(microseconds=1))
                         ["rows"][0]["close"], 100)
        for field in ("published", "observed", "received", "ingested", "verified"):
            for value in (None, self.cutoff, self.cutoff + timedelta(days=1)):
                with self.subTest(field=field, value=value):
                    bars = [replace(original, clocks=replace(original.clocks, **{field: value}))]
                    self.assertIsNone(self.table(bars=bars)["rows"][0]["close"])

    def test_revision_and_future_append_cannot_change_frozen_snapshot(self):
        before = tuple(b for b in self.bars if b.clocks.available_before(self.cutoff))
        frozen = self.table(bars=before)
        serialized = json.dumps(frozen, sort_keys=True)
        self.assertEqual(frozen, self.table())
        later = self.table(cutoff=self.sessions[-1] + timedelta(seconds=10))
        self.assertEqual(later["rows"][4]["close"], 103)
        self.assertEqual(later["rows"][4]["evidence_id"], "synthetic:bar:4:r2")
        self.assertEqual(json.dumps(frozen, sort_keys=True), serialized)
        self.assertEqual(frozen["rows"][4]["close"], 104)
        self.assertEqual(frozen["rows"][5]["input_versions"][-2], "synthetic:bar:4:r1")

    def test_gaps_and_null_volume_are_never_filled(self):
        rows = self.table(cutoff=self.sessions[-1] + timedelta(seconds=10))["rows"]
        for index in (6, 10, 11):
            self.assertEqual(rows[index]["status"], "missing_or_unavailable")
            self.assertIsNone(rows[index]["close"])
        self.assertIsNone(rows[7]["sma_3"])
        self.assertIsNone(rows[9]["volume_change"])
        self.assertIsNone(rows[12]["volatility_3"])
        self.assertIsNotNone(rows[15]["volatility_3"])

    def test_zero_volume_has_no_infinite_ratio(self):
        bars = [replace(b, volume=0) for b in self.bars]
        rows = self.table(bars=bars)["rows"]
        self.assertIsNone(rows[5]["volume_change"])
        self.assertIsNone(rows[5]["volume_ratio_3"])

    def test_naive_clocks_and_duplicate_versions_fail_closed(self):
        with self.assertRaises(ValueError):
            self.table(cutoff=self.cutoff.replace(tzinfo=None))
        with self.assertRaises(ValueError):
            self.table(bars=self.bars + (self.bars[0],))
        with self.assertRaises(ValueError):
            self.table(bars=(replace(self.bars[0], close=float("nan")),))

    def test_chart_does_not_rescale_from_future_data(self):
        short = self.table()
        before = demo.chart_view(short)
        extreme = tuple(replace(b, high=100000, close=99999) if b.end > self.cutoff else b
                        for b in self.bars)
        self.assertEqual(demo.chart_view(self.table(bars=extreme)), before)
        self.assertIn("fixed axis", before)


class StatementTests(unittest.TestCase):
    def setUp(self):
        self.statements = demo.statement_fixture()
        self.cutoff = self.statements[1].clocks.verified + timedelta(seconds=1)

    def snapshot(self, versions=None, cutoff=None):
        return demo.statement_snapshot(self.statements if versions is None else versions,
                                       self.cutoff if cutoff is None else cutoff)

    def test_numeric_change_and_exact_source_spans(self):
        result = self.snapshot()
        self.assertEqual(result["rate_change_pp"], ["-0.25", "-0.25"])
        self.assertEqual(result["selected"]["evidence_id"], "synthetic:fomc:B:r1")
        for record in result["versions"]:
            raw = record["text"].encode("utf-8")
            for fact in record["rate_facts"]:
                start, end = fact["byte_span"]
                self.assertEqual(raw[start:end].decode("utf-8"), fact["value"])
                self.assertEqual(fact["artifact_sha256"], record["raw_sha256"])
        self.assertIn("-Inflation remains elevated.", result["text_diff"])
        self.assertIn("+Inflation has eased.", result["text_diff"])
        self.assertEqual(result["selected"]["terms"]["eased"][0]["text"], "eased")

    def test_publication_and_future_effective_time_do_not_replace_receipt(self):
        second = self.statements[1]
        self.assertGreater(second.effective, self.cutoff)
        self.assertEqual(self.snapshot()["selected"]["evidence_id"], second.evidence_id)
        at_publication = self.snapshot(cutoff=second.clocks.published + timedelta(microseconds=1))
        self.assertEqual(at_publication["selected"]["event_id"], "synthetic:fomc:A")
        at_verification = self.snapshot(cutoff=second.clocks.verified)
        self.assertEqual(at_verification["selected"]["event_id"], "synthetic:fomc:A")

    def test_late_correction_preserves_original_and_prior_bundle(self):
        frozen = self.snapshot(versions=self.statements[:2])
        self.assertEqual(frozen, self.snapshot())
        revision = self.statements[2]
        late = self.snapshot(cutoff=revision.clocks.verified + timedelta(seconds=1))
        self.assertEqual(late["selected"]["evidence_id"], revision.evidence_id)
        self.assertEqual(late["rate_change_pp"], ["-0.50", "-0.50"])
        self.assertEqual(late["revision_change_pp"], ["-0.25", "-0.25"])
        self.assertEqual(len(late["versions"]), 3)
        self.assertEqual(frozen["selected"]["evidence_id"], "synthetic:fomc:B:r1")
        self.assertNotIn("Corrected", json.dumps(frozen))
        self.assertEqual(revision.previous_version, "synthetic:fomc:B:r1")
        self.assertIn("-Target range: 4.25 to 4.50 percent.", late["revision_text_diff"])
        self.assertIn("+Target range: 4.00 to 4.25 percent.", late["revision_text_diff"])

    def test_revision_clock_also_gates_correction(self):
        correction = self.statements[2]
        late = correction.clocks.verified + timedelta(seconds=1)
        versions = self.statements[:2] + (replace(correction, clocks=replace(
            correction.clocks, revised=late + timedelta(days=1))),)
        self.assertEqual(self.snapshot(versions=versions, cutoff=late)["selected"]
                         ["evidence_id"], "synthetic:fomc:B:r1")

    def test_unknown_receipt_or_missing_rate_abstains(self):
        second = self.statements[1]
        unknown = replace(second, clocks=replace(second.clocks, received=None))
        self.assertEqual(self.snapshot(versions=(self.statements[0], unknown))["selected"]
                         ["event_id"], "synthetic:fomc:A")
        missing = replace(second, text="Synthetic statement. No numeric range supplied.")
        result = self.snapshot(versions=(self.statements[0], missing))
        self.assertIsNone(result["rate_change_pp"])
        self.assertEqual(result["selected"]["rate_status"], "unavailable")


class ReproducibilityTests(unittest.TestCase):
    def test_cli_is_repeatable_offline_and_refuses_overwrite(self):
        with tempfile.TemporaryDirectory() as directory:
            outputs = [Path(directory) / name for name in ("first", "second")]
            for output in outputs:
                guard = ("import runpy,socket,sys,urllib.request; "
                         "deny=lambda *a,**k: (_ for _ in ()).throw(AssertionError('network forbidden')); "
                         "socket.socket=deny; socket.create_connection=deny; urllib.request.urlopen=deny; "
                         "sys.argv=['offline_chart_gov_demo']+sys.argv[1:]; "
                         "runpy.run_module('agent.offline_chart_gov_demo',run_name='__main__')")
                result = subprocess.run([sys.executable, "-c", guard,
                                         "--output", str(output)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 0, result.stderr)
            for name in ("snapshot.json", "chart.txt"):
                self.assertEqual((outputs[0] / name).read_bytes(),
                                 (outputs[1] / name).read_bytes())
            packet = json.loads((outputs[0] / "snapshot.json").read_text(encoding="utf-8"))
            self.assertEqual(packet["scope"], "SYNTHETIC_OFFLINE_ONLY")
            self.assertEqual(packet["model_calls"], 0)
            result = subprocess.run([sys.executable, "-m", "agent.offline_chart_gov_demo",
                                     "--output", str(outputs[0])], capture_output=True, text=True)
            self.assertNotEqual(result.returncode, 0)

    def test_benchmark_reports_fixed_sample_sizes_and_units(self):
        measured = demo.benchmark(sizes=(30,), repetitions=3)
        self.assertEqual(measured["cases"][0]["rows"], 30)
        self.assertGreater(measured["cases"][0]["peak_tracemalloc_bytes"], 0)
        self.assertLessEqual(measured["cases"][0]["p50_seconds"],
                             measured["cases"][0]["p95_seconds"])
        self.assertEqual(measured["repetitions"], 3)


if __name__ == "__main__":
    unittest.main()
