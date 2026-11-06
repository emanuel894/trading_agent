"""Authentic M02 facts and explicitly synthetic corruption/format counterexamples."""
from datetime import datetime, timedelta, timezone
import gzip
import json
from pathlib import Path
import tempfile
import unittest

try:
    from agent import fed_statement_offline as fed
except ImportError:
    fed = None


SOURCE = Path(__file__).resolve().parents[2] / "docs/event-evidence/sources"
RETRIEVED = datetime(2026, 10, 18, 8, 0, 10, 273966, tzinfo=timezone.utc)


class RetainedFedTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(fed, "The retained-format offline adapter is not implemented")
        self.document = fed.load_retained()

    def snapshot(self):
        return self.document.snapshot(RETRIEVED + timedelta(seconds=1))

    def test_authentic_fractional_range_excludes_inflation_and_dissent_numbers(self):
        result = self.snapshot()
        self.assertEqual(result["status"], "CATALOG_FACTS_ONLY")
        self.assertEqual([x["value"] for x in result["facts"]["target_range"]], ["4.75", "5"])
        self.assertEqual([x["unit"] for x in result["facts"]["target_range"]], ["percent", "percent"])
        self.assertEqual(result["facts"]["policy_markers"]["balance_sheet_reduction"][0]["text"],
                         "continue reducing its holdings")

    def test_every_fact_span_round_trips_to_retained_utf8_bytes(self):
        facts = self.snapshot()["facts"]
        spans = facts["target_range"] + [x for v in facts["policy_markers"].values() for x in v]
        self.assertTrue(spans)
        for item in spans:
            a, b = item["raw_utf8_bytes"]
            self.assertEqual(self.document.raw[a:b].decode("utf-8"), item["text"])
            self.assertEqual(item["artifact_sha256"],
                             "af7d78c3516a12e6fc03a4db92d9fe610a5bbbdf9619e880df28fdc92aa882fd")

    def test_missing_independent_prior_stops_comparisons_without_backsolving(self):
        result = self.snapshot()
        self.assertIsNone(result["facts"]["rate_change_pp"])
        self.assertIsNone(result["facts"]["statement_diff"])
        self.assertEqual(result["comparison_status"], "ABSTAIN_MISSING_INDEPENDENT_PRIOR")

    def test_original_edition_and_historical_receipt_remain_unknown(self):
        result = self.snapshot()
        self.assertEqual(result["mode"], "catalog_only")
        self.assertEqual(result["predictive_admission"], "quarantined")
        self.assertFalse(result["original_edition_proven"])
        for clock in ("first_machine_observable", "first_receipt", "source_revision",
                      "economic_effective", "ingestion_completed", "verification_completed"):
            self.assertEqual(result["clocks"][clock]["state"], "unknown")
            self.assertIsNone(result["clocks"][clock]["utc"])
        self.assertEqual(result["clocks"]["official_publication"]["precision"], "minute")
        self.assertIsNone(result["clocks"]["official_publication"]["utc"])
        self.assertEqual(result["clocks"]["retrieved"]["native_value"],
                         "2026-10-18T08:00:10.273966+00:00")

    def test_release_labels_carry_raw_source_spans_without_invented_seconds(self):
        clock = self.snapshot()["clocks"]["official_publication"]
        self.assertEqual(clock["native_date"], "September 18, 2024")
        self.assertEqual(clock["native_value"], "For release at 2:00 p.m. EDT")
        for span in clock["evidence"]:
            a, b = span["raw_utf8_bytes"]
            self.assertEqual(self.document.raw[a:b].decode("utf-8"), span["text"])
        self.assertEqual(len(clock["evidence"]), 2)

    def test_catalog_cutoff_uses_retrieval_strictly_not_release_label(self):
        for cutoff in (datetime(2024, 9, 19, tzinfo=timezone.utc), RETRIEVED):
            result = self.document.snapshot(cutoff)
            self.assertEqual(result["status"], "ABSTAIN_NOT_RETRIEVED_BEFORE_CUTOFF")
            self.assertIsNone(result["facts"])
        with self.assertRaises(ValueError):
            self.document.snapshot(RETRIEVED.replace(tzinfo=None))

    def test_failed_source_verification_never_uses_modified_or_missing_bytes(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root)
            for name in ("captures.json", "M02.raw.gz"):
                (destination / name).write_bytes((SOURCE / name).read_bytes())
            (destination / "M02.raw.gz").write_bytes(gzip.compress(b"unverified replacement"))
            with self.assertRaises(ValueError):
                fed.load_retained(destination)
            (destination / "M02.raw.gz").unlink()
            with self.assertRaises(FileNotFoundError):
                fed.load_retained(destination)

    def test_modified_manifest_cannot_self_certify_a_revision(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root)
            manifest = json.loads((SOURCE / "captures.json").read_bytes())
            next(x for x in manifest if x["id"] == "M02")["retrieved_at"] = "2024-09-18T18:00:00Z"
            (destination / "captures.json").write_text(json.dumps(manifest), encoding="utf-8")
            (destination / "M02.raw.gz").write_bytes((SOURCE / "M02.raw.gz").read_bytes())
            with self.assertRaises(ValueError):
                fed.load_retained(destination)

    def test_late_replacement_cannot_mutate_loaded_earlier_cutoff_view(self):
        with tempfile.TemporaryDirectory() as root:
            destination = Path(root)
            for name in ("captures.json", "M02.raw.gz"):
                (destination / name).write_bytes((SOURCE / name).read_bytes())
            loaded = fed.load_retained(destination)
            cutoff = RETRIEVED + timedelta(seconds=1)
            frozen = loaded.snapshot(cutoff)
            frozen_bytes = json.dumps(frozen, sort_keys=True)
            (destination / "M02.raw.gz").write_bytes(gzip.compress(
                loaded.raw.replace(b"4-3/4 to 5 percent", b"3-3/4 to 4 percent")))
            self.assertEqual(loaded.snapshot(cutoff), frozen)
            self.assertEqual(json.dumps(frozen, sort_keys=True), frozen_bytes)
            with self.assertRaises(ValueError):
                fed.load_retained(destination)


class ExplicitSyntheticFormatTests(unittest.TestCase):
    """Unqualified text-parser probes, never replacement authentic source evidence."""
    def setUp(self):
        self.assertIsNotNone(fed, "The retained-format offline adapter is not implemented")
        self.raw = gzip.decompress((SOURCE / "M02.raw.gz").read_bytes())

    def test_malformed_units_conflicts_fractions_and_markup_abstain(self):
        original = b"4-3/4 to 5 percent"
        variants = [b"4-3/4 to 5 basis points", b"4-3/0 to 5 percent",
                    b"6 to 5 percent", b"4-3/4 to <span>5</span> percent"]
        variants.append(b"4-3/4 to 5 percent. The Committee decided to maintain the target range "
                        b"for the federal funds rate at 6 to 7 percent")
        for replacement in variants:
            with self.subTest(replacement=replacement):
                with self.assertRaises(ValueError):
                    fed._parse_policy(self.raw.replace(original, replacement))

    def test_unicode_before_range_preserves_raw_byte_span(self):
        raw = self.raw.replace(b"In light of", "\u03c0 In light of".encode("utf-8"))
        facts = fed._parse_policy(raw)
        item = facts["target_range"][0]
        a, b = item["raw_utf8_bytes"]
        self.assertEqual(raw[a:b], b"4-3/4")

    def test_missing_article_or_policy_sentence_is_not_a_zero_rate(self):
        for raw in (b"not HTML", self.raw.replace(b"Committee decided to", b"Committee considered")):
            with self.subTest(raw_length=len(raw)):
                with self.assertRaises(ValueError):
                    fed._parse_policy(raw)


if __name__ == "__main__":
    unittest.main()
