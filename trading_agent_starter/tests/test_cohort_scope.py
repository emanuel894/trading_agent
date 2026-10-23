"""Scope selection is metadata-only, deterministic and non-replacing."""
from datetime import date
from io import BytesIO
from pathlib import Path
import tempfile
import unittest
from zipfile import ZipFile

from agent.audit_store import AuditFailure, EvidenceStore, canonical, digest, strict_json, timestamp
from agent.cohort_scope import build_scope, freeze_scope, index_candidates, sessions_2025h1


class CohortTests(unittest.TestCase):
    def fixture(self):
        lines, metadata = [], {}
        for cik in range(1, 27):
            key = str(cik).zfill(10)
            metadata[key] = []
            for j, day in enumerate(("2025-01-08", "2025-04-18", "2025-05-01")):
                accession = f"{cik:010d}-25-{j:06d}"
                lines.append(f"{cik}|Fixture|10-Q|{day}|edgar/data/{cik}/{accession}.txt")
                metadata[key].append(dict(cik=key, accession=accession, form="10-Q",
                    accepted_at=day+"T21:00:00Z", report_date="2024-12-31", observation_id="synthetic"))
        lines.append("1|Fixture|10-Q/A|2025-01-01|edgar/data/1/0000000001-25-999999.txt")
        out = BytesIO()
        with ZipFile(out, "w") as archive:
            archive.writestr("master.idx", "\n".join(reversed(lines)))
        return index_candidates([out.getvalue()]), metadata

    def test_fixed_ciks_and_earliest_original_two_ignore_input_order(self):
        candidates, metadata = self.fixture()
        scope = build_scope(candidates, metadata, "0"*64, [{"source": "synthetic"}])
        self.assertEqual(len(scope["targets"]), 50)
        self.assertEqual(len({t["cik"] for t in scope["targets"]}), 25)
        self.assertNotIn("0000000026", candidates)
        self.assertTrue(all(t["accession"].endswith(("000000", "000001")) for t in scope["targets"]))
        self.assertEqual(scope["targets"][0]["actionable_at"], "2025-01-10T14:35:00+00:00")
        self.assertEqual(scope["targets"][1]["actionable_at"], "2025-04-21T13:35:00+00:00")
        self.assertEqual({t["actionable_at"] for t in scope["targets"]},
                         {t["actionable_at"] for t in scope["context_instruments"]})
        metadata["0000000001"].pop()
        with self.assertRaisesRegex(AuditFailure, "MISMATCH_NO_REPLACEMENT"):
            build_scope(candidates, metadata, "0"*64, [])

    def test_manifest_is_content_hashed_and_cannot_be_silently_refrozen(self):
        candidates, metadata = self.fixture()
        scope = build_scope(candidates, metadata, "0"*64, [])
        with tempfile.TemporaryDirectory() as tmp:
            store = EvidenceStore(Path(tmp)/"evidence")
            try:
                output = Path(tmp)/"manifest.json"
                result = freeze_scope(scope, store, output)
                self.assertEqual(result["scope_sha256"], digest(canonical(scope)))
                self.assertEqual(result["file_sha256"], digest(output.read_bytes()))
                self.assertFalse(strict_json(output.read_bytes())["audit_executed"])
                with self.assertRaisesRegex(AuditFailure, "EXPLICIT_AMENDMENT"):
                    freeze_scope(scope, store, output)
                self.assertEqual(len(store.records("frozen_cohort_manifest")), 1)
            finally:
                store.close()

    def test_calendar_closures_and_early_close(self):
        sessions = {a.date(): (a, b) for a, b in sessions_2025h1()}
        self.assertNotIn(date(2025, 1, 9), sessions)
        self.assertNotIn(date(2025, 4, 18), sessions)
        self.assertNotIn(date(2025, 6, 19), sessions)
        self.assertEqual(sessions[date(2025, 7, 3)][1], timestamp("2025-07-03T17:00:00Z"))


if __name__ == "__main__":
    unittest.main()
