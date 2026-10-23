"""Metadata-only frame integrity tests. No live requests or issuer screening."""
from io import BytesIO
import unittest
from zipfile import ZipFile
from pathlib import Path

from agent.acquisition_frame_replay import original_rows, reconcile
from agent.acquisition_registration import check_ledger_prefix, priority_order
from agent.audit_store import AuditFailure, canonical, digest, strict_json


class FrameReplayTests(unittest.TestCase):
    def archive(self, lines):
        output = BytesIO()
        with ZipFile(output, "w") as archive:
            archive.writestr("master.idx", "CIK|Company Name|Form Type|Date Filed|Filename\n" + "\n".join(lines))
        return output.getvalue()

    def row(self, form="10-Q", day="2025-05-09", path_cik="9000000001"):
        return f"9000000001|SYNTHETIC|{form}|{day}|edgar/data/{path_cik}/9000000001-25-000001.txt"

    def test_exact_original_form_and_quarter_only(self):
        rows = original_rows(self.archive([self.row(), self.row("10-Q/A")]), 2)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["cik"], "9000000001")
        for raw in (self.archive([self.row(day="2024-05-09")]),
                    self.archive([self.row(day="2025-08-09")])):
            with self.assertRaisesRegex(AuditFailure, "OUTSIDE_REGISTERED_QUARTER"):
                original_rows(raw, 2)

    def test_index_cik_must_match_path(self):
        with self.assertRaisesRegex(AuditFailure, "CIK_OR_ACCESSION_CONFLICT"):
            original_rows(self.archive([self.row(path_cik="9000000002")]), 2)

    def test_reconcile_exact_pairs_and_ciks(self):
        rows = original_rows(self.archive([self.row()]), 2)
        pair = {k: rows[0][k] for k in ("cik", "accession")}
        pairs, ciks, normalized = reconcile([rows], [pair], 1, 1)
        self.assertEqual(pairs, [pair])
        self.assertEqual(ciks, [pair["cik"]])
        self.assertEqual(normalized[0]["index_references"], [{"quarter": 2, "line": 2}])
        for counts in ((2, 1), (1, 2)):
            with self.assertRaisesRegex(AuditFailure, "FRAME_COUNT_MISMATCH"):
                reconcile([rows], [pair], *counts)
        changed = dict(pair, accession="9000000001-25-000002")
        with self.assertRaisesRegex(AuditFailure, "PAIR_SET_OR_ORDER_MISMATCH"):
            reconcile([rows], [changed], 1, 1)

    def test_duplicate_references_retained_but_conflicts_rejected(self):
        row = original_rows(self.archive([self.row()]), 2)[0]
        pair = {k: row[k] for k in ("cik", "accession")}
        _, _, normalized = reconcile([[row, dict(row, line=3)]], [pair], 1, 1)
        self.assertEqual(len(normalized[0]["index_references"]), 2)
        with self.assertRaisesRegex(AuditFailure, "CONFLICTING_DUPLICATE_ORIGINAL"):
            reconcile([[row, dict(row, issuer_index_name="UNRELATED")]], [pair], 1, 1)

    def test_frozen_priority_bytes_and_single_blocking_ledger(self):
        root = Path(__file__).resolve().parents[1]
        raw = (root / "research/acquisition_priority_order_004.json").read_bytes()
        self.assertEqual(digest(raw), "f90430aeb8c92031317e376080142e3513bb648dc64522cec6c0d526fdc59a69")
        order = strict_json(raw)
        self.assertEqual(len(order), 5974)
        self.assertEqual(raw, canonical(order))
        registration = (root / "research/acquisition_frame_registration_004.json").read_bytes()
        self.assertEqual(order, priority_order([r["cik"] for r in order], registration))
        ledger = strict_json((root / "research/acquisition_candidate_001_004_ledger.json").read_bytes())
        self.assertEqual(len(ledger["entries"]), 1)
        result = check_ledger_prefix([r["cik"] for r in order], ledger["entries"], registration)
        self.assertEqual(result, ledger["validation"])
        self.assertEqual((result["status"], result["priority"], result["cik"]),
                         ("BLOCKED", 1, "0000700565"))


if __name__ == "__main__":
    unittest.main()
