"""Offline regression and interruption tests for the shared evidence store."""
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from agent.audit_store import AuditFailure, EvidenceStore, digest


class AtomicStoreTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.store = EvidenceStore(Path(self.tmp.name))

    def tearDown(self):
        self.store.close()
        self.tmp.cleanup()

    def test_explicit_transaction_rolls_back_evidence_and_queue_together(self):
        self.store.db.execute("CREATE TABLE jobs (id TEXT PRIMARY KEY)")
        with self.assertRaisesRegex(RuntimeError, "crash"):
            with self.store.transaction():
                self.store.append_in_transaction("fixture", "one", {}, b"raw")
                self.store.db.execute("INSERT INTO jobs VALUES ('one')")
                raise RuntimeError("crash")
        self.assertEqual(self.store.records(), [])
        self.assertEqual(self.store.db.execute("SELECT count(*) FROM jobs").fetchone()[0], 0)
        self.assertEqual((self.store.objects / digest(b"raw")).read_bytes(), b"raw")

    def test_standalone_api_still_commits_versions_and_deduplicates(self):
        first = self.store.append("fixture", "one", {}, b"raw")
        second = self.store.append("fixture", "one", {}, b"raw")
        self.assertEqual(second["previous_version"], first["id"])
        self.assertEqual(len(list(self.store.objects.iterdir())), 1)
        self.assertEqual(self.store.verify()["records"], 2)
        with self.assertRaises(sqlite3.IntegrityError):
            self.store.db.execute("DELETE FROM records")
        self.store.db.rollback()

    def test_partial_spool_never_becomes_final_object(self):
        with patch("agent.audit_store.os.fsync", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.store.append("fixture", "one", {}, b"complete")
        self.assertFalse((self.store.objects / digest(b"complete")).exists())
        self.assertEqual(self.store.records(), [])
        self.assertTrue(list(self.store.spool.iterdir()))

    def test_final_object_survives_interruption_without_evidence_commit(self):
        original = self.store._finalize_blob
        def crash(raw):
            original(raw)
            raise SystemExit("crash")
        with patch.object(self.store, "_finalize_blob", side_effect=crash):
            with self.assertRaises(SystemExit):
                self.store.append("fixture", "one", {}, b"complete")
        self.assertEqual(self.store.records(), [])
        self.assertEqual((self.store.objects / digest(b"complete")).read_bytes(), b"complete")

    def test_existing_corrupt_hash_is_never_overwritten(self):
        raw = b"known"
        path = self.store.objects / digest(raw)
        path.write_bytes(b"corrupt")
        with self.assertRaisesRegex(AuditFailure, "BLOB_HASH_MISMATCH"):
            self.store.append("fixture", "one", {}, raw)
        self.assertEqual(path.read_bytes(), b"corrupt")
        self.assertEqual(self.store.records(), [])

    def test_transaction_api_rejects_missing_or_nested_transaction(self):
        with self.assertRaisesRegex(AuditFailure, "TRANSACTION_REQUIRED"):
            self.store.append_in_transaction("fixture", "one", {})
        with self.store.transaction():
            with self.assertRaisesRegex(AuditFailure, "NESTED_TRANSACTION"):
                with self.store.transaction():
                    pass
