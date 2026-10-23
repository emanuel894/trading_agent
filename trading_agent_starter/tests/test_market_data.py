from dataclasses import replace
from datetime import datetime, timedelta, timezone
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from agent.market_data import (
    HistoryRequest, INTERVAL, RawBar, Session, normalize_bars, write_snapshot,
)


def dt(value):
    return datetime.fromisoformat(value)


def request(**changes):
    base = HistoryRequest(("SPY", "QQQ"), dt("2026-09-14T13:30:00Z"),
                          dt("2026-09-14T15:00:00Z"), dt("2026-09-14T15:01:00Z"))
    return replace(base, **changes)


def rows(req=None):
    req = req or request()
    return [RawBar(s, req.start + INTERVAL * i, 100, 102, 99, 101, 1000)
            for s in req.symbols for i in range(3)]


def snapshot(data=None, req=None, sessions=None):
    req = req or request()
    return normalize_bars(req, sessions if sessions is not None else [Session(
        dt("2026-09-14T13:30:00Z"), dt("2026-09-14T20:00:00Z"))],
        rows(req) if data is None else data, source="fixture", feed="iex")


class ContractTests(unittest.TestCase):
    def test_symbol_and_timezone_normalization_is_deterministic(self):
        req = request(symbols=(" spy ", "qqq", "SPY"), start=dt("2026-09-14T09:30:00-04:00"))
        a = snapshot(rows(), req)
        b = snapshot(list(reversed(rows())), req)
        self.assertTrue(a.ready)
        self.assertEqual(a.bars, b.bars)
        self.assertEqual(req.symbols, ("QQQ", "SPY"))
        self.assertEqual(a.bars[0].timestamp.tzinfo, timezone.utc)

    def test_invalid_requests_rejected(self):
        for changes in ({"symbols": ()}, {"symbols": ("",)}, {"symbols": "SPY"},
                        {"symbols": tuple(f"S{i}" for i in range(21))},
                        {"start": dt("2026-09-14T13:30:00")},
                        {"end": dt("2026-09-14T15:02:00Z")},
                        {"end": dt("2026-09-14T13:30:00Z")},
                        {"start": dt("2024-01-01T00:00:00Z")},
                        {"publication_delay_seconds": -1}, {"publication_delay_seconds": True}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                request(**changes)

    def test_missing_symbol_never_silently_dropped(self):
        data = snapshot([b for b in rows() if b.symbol == "SPY"])
        self.assertFalse(data.ready)
        self.assertEqual(len(data.quality()["symbols"]["QQQ"]["missing_intervals"]), 3)
        with self.assertRaises(ValueError):
            data.require_ready()

    def test_internal_gap_blocks_even_when_latest_bar_is_fresh(self):
        data = snapshot([b for b in rows() if not (b.symbol == "SPY" and b.timestamp.hour == 14 and b.timestamp.minute == 0)])
        self.assertFalse(data.ready)
        self.assertFalse(data.quality()["symbols"]["SPY"]["stale"])

    def test_stale_latest_bar_detected_per_symbol(self):
        data = snapshot(rows()[:-1])
        self.assertTrue(data.quality()["symbols"]["SPY"]["stale"])
        self.assertFalse(data.quality()["symbols"]["QQQ"]["stale"])

    def test_closed_bar_waits_for_publication_delay(self):
        for cutoff, expected in (("2026-09-14T15:00:00Z", 4), ("2026-09-14T15:00:59Z", 4),
                                 ("2026-09-14T15:01:00Z", 6)):
            with self.subTest(cutoff=cutoff):
                data = snapshot(req=request(as_of=dt(cutoff)))
                self.assertTrue(data.ready)
                self.assertEqual(len(data.bars), expected)

    def test_partial_bar_and_exclusive_end_are_not_visible(self):
        req = request(end=dt("2026-09-14T14:45:00Z"), as_of=dt("2026-09-14T14:45:00Z"))
        self.assertEqual(len(snapshot(req=req).bars), 4)
        edge = replace(rows()[0], timestamp=request().end)
        self.assertEqual(snapshot(rows() + [edge]).bars, snapshot().bars)

    def test_future_price_changes_do_not_change_earlier_inputs(self):
        baseline = snapshot()
        modified = snapshot([replace(b, open=900, high=999, low=800, close=950)
                             if b.timestamp >= dt("2026-09-14T14:30:00Z") else b for b in rows()])
        cutoff = dt("2026-09-14T14:31:00Z")
        self.assertEqual(baseline.visible_at(cutoff), modified.visible_at(cutoff))
        self.assertEqual(len(baseline.visible_at(cutoff)), 4)
        with self.assertRaises(ValueError):
            baseline.visible_at(dt("2026-09-14T15:02:00Z"))

    def test_invalid_in_progress_prices_cannot_affect_completed_snapshot(self):
        req = request(end=dt("2026-09-14T14:45:00Z"), as_of=dt("2026-09-14T14:45:00Z"))
        changed = [replace(b, close=float("nan")) if b.timestamp.minute == 30 and b.timestamp.hour == 14 else b for b in rows()]
        self.assertEqual(snapshot(changed, req).bars, snapshot(rows(), req).bars)

    def test_extended_hours_removed(self):
        req = request(start=dt("2026-09-14T00:00:00Z"), end=dt("2026-09-15T00:00:00Z"), as_of=dt("2026-09-15T00:01:00Z"))
        extended = [replace(rows()[0], timestamp=dt(t)) for t in ("2026-09-14T13:00:00Z", "2026-09-14T20:00:00Z")]
        data = snapshot(rows() + extended, req)
        self.assertEqual(dict(data.excluded)["outside_session"], 2)
        self.assertEqual(len(data.bars), 6)

    def test_holiday_weekend_and_early_close_do_not_create_false_gaps(self):
        req = request(start=dt("2026-11-26T00:00:00Z"), end=dt("2026-11-30T00:00:00Z"), as_of=dt("2026-11-30T00:01:00Z"))
        session = Session(dt("2026-11-27T14:30:00Z"), dt("2026-11-27T18:00:00Z"))
        data = [replace(rows()[0], symbol=s, timestamp=session.open + i * INTERVAL) for s in req.symbols for i in range(7)]
        result = snapshot(data, req, [session])
        self.assertTrue(result.ready)
        self.assertEqual(len(result.bars), 14)

    def test_empty_window_is_not_a_pass(self):
        result = snapshot([], sessions=[])
        self.assertFalse(result.ready)
        self.assertFalse(result.quality()["symbols"]["SPY"]["stale"])

    def test_duplicates_collapse_identical_but_reject_conflicting(self):
        self.assertEqual(snapshot(rows() + [rows()[0]]).bars, snapshot().bars)
        self.assertEqual(dict(snapshot(rows() + [rows()[0]]).excluded)["identical_duplicate"], 1)
        with self.assertRaisesRegex(ValueError, "Conflicting"):
            snapshot(rows() + [replace(rows()[0], close=100.5)])

    def test_invalid_price_volume_timestamp_or_symbol_rejected(self):
        for changes in ({"close": float("nan")}, {"volume": float("inf")}, {"low": 101},
                        {"high": 100}, {"volume": -1}, {"open": 0}, {"symbol": "UNKNOWN"},
                        {"timestamp": dt("2026-09-14T13:31:00Z")},
                        {"timestamp": dt("2026-09-14T13:30:00")}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                snapshot([replace(rows()[0], **changes)] + rows()[1:])

    def test_bad_calendar_and_adjustments_rejected(self):
        session = snapshot().sessions[0]
        with self.assertRaises(ValueError):
            snapshot(sessions=[session, session])
        with self.assertRaises(ValueError):
            Session(session.close, session.open)
        with self.assertRaises(ValueError):
            normalize_bars(request(), [session], rows(), source="fixture", feed="iex", adjustment="all")


class SnapshotTests(unittest.TestCase):
    def test_export_is_deterministic_hashed_and_has_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            a, b = Path(directory) / "a", Path(directory) / "b"
            stamp = dt("2026-09-15T00:00:00Z")
            manifest = write_snapshot(snapshot(), a, retrieved_at=stamp)
            write_snapshot(snapshot(list(reversed(rows()))), b, retrieved_at=stamp)
            for name in ("bars.csv", "manifest.json"):
                self.assertEqual((a / name).read_bytes(), (b / name).read_bytes())
            self.assertEqual(manifest["bars_sha256"], hashlib.sha256((a / "bars.csv").read_bytes()).hexdigest())
            self.assertEqual(manifest["adjustment"], "raw")
            self.assertEqual(manifest["publication_delay_seconds"], 60)
            self.assertEqual(json.loads((a / "manifest.json").read_text()), manifest)
            self.assertNotIn("secret", (a / "manifest.json").read_text())
            with self.assertRaisesRegex(ValueError, "already exists"):
                write_snapshot(snapshot(), a, retrieved_at=stamp)

    def test_write_failure_does_not_publish_partial_snapshot(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "snapshot"
            with patch.object(Path, "write_text", side_effect=OSError("disk full")):
                with self.assertRaises(OSError):
                    write_snapshot(snapshot(), output, retrieved_at=request().as_of)
            self.assertFalse(output.exists())
            self.assertEqual(list(Path(directory).iterdir()), [])

    def test_future_retrieval_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory, self.assertRaises(ValueError):
            write_snapshot(snapshot(), Path(directory) / "bad", retrieved_at=request().start)


if __name__ == "__main__":
    unittest.main()
