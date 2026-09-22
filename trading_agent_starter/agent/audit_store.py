"""Append-only audit evidence. No broker, strategy, model or executable documents."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import uuid

VERSION = "10q-audit-v1"


class AuditFailure(RuntimeError):
    """A stable reason code; never include credentials or arbitrary HTTP errors."""


def utc_now():
    return datetime.now(timezone.utc).isoformat()


def timestamp(value):
    if not isinstance(value, str):
        raise AuditFailure("INVALID_TIMESTAMP")
    try:
        result = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        raise AuditFailure("INVALID_TIMESTAMP") from None
    if result.utcoffset() is None:
        raise AuditFailure("NAIVE_TIMESTAMP")
    return result.astimezone(timezone.utc)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("utf-8")


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def strict_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise AuditFailure("DUPLICATE_JSON_KEY")
            result[key] = value
        return result

    def invalid(_):
        raise AuditFailure("NONFINITE_JSON")

    try:
        return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid)
    except (ValueError, UnicodeError, RecursionError):
        raise AuditFailure("MALFORMED_JSON") from None


class EvidenceStore:
    def __init__(self, root):
        self.root = Path(root)
        self.objects = self.root / "objects"
        self.objects.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.root / "evidence.sqlite", timeout=30)
        self.db.execute("PRAGMA foreign_keys=ON")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS records (
              seq INTEGER PRIMARY KEY, id TEXT NOT NULL UNIQUE,
              kind TEXT NOT NULL, source_key TEXT NOT NULL,
              recorded_at TEXT NOT NULL, blob_sha TEXT,
              previous_version TEXT REFERENCES records(id),
              previous_chain TEXT, record_hash TEXT NOT NULL,
              metadata TEXT NOT NULL);
            CREATE INDEX IF NOT EXISTS versions ON records(kind, source_key, seq);
            CREATE TRIGGER IF NOT EXISTS no_update BEFORE UPDATE ON records
              BEGIN SELECT RAISE(ABORT, 'IMMUTABLE_EVIDENCE'); END;
            CREATE TRIGGER IF NOT EXISTS no_delete BEFORE DELETE ON records
              BEGIN SELECT RAISE(ABORT, 'IMMUTABLE_EVIDENCE'); END;
        """)
        self.db.row_factory = sqlite3.Row

    def close(self):
        self.db.close()

    def append(self, kind, key, metadata, raw=None):
        # Serialize first so bad metadata cannot leave a partly committed record.
        metadata = strict_json(canonical(metadata))
        with self.db:
            self.db.execute("BEGIN IMMEDIATE")
            previous = self.db.execute(
                "SELECT id FROM records WHERE kind=? AND source_key=? ORDER BY seq DESC LIMIT 1",
                (kind, key)).fetchone()
            chain = self.db.execute("SELECT record_hash FROM records ORDER BY seq DESC LIMIT 1").fetchone()
            sha = digest(raw) if raw is not None else None
            if sha:
                path = self.objects / sha
                try:
                    with path.open("xb") as handle:
                        handle.write(raw)
                        handle.flush()
                        os.fsync(handle.fileno())
                except FileExistsError:
                    if digest(path.read_bytes()) != sha:
                        raise AuditFailure("BLOB_HASH_MISMATCH") from None
            envelope = dict(id=uuid.uuid4().hex, kind=kind, source_key=key,
                            recorded_at=utc_now(), blob_sha=sha,
                            previous_version=previous[0] if previous else None,
                            previous_chain=chain[0] if chain else None, metadata=metadata)
            record_hash = digest(canonical(envelope))
            self.db.execute("""INSERT INTO records
                (id,kind,source_key,recorded_at,blob_sha,previous_version,previous_chain,record_hash,metadata)
                VALUES (?,?,?,?,?,?,?,?,?)""", (
                envelope["id"], kind, key, envelope["recorded_at"], sha,
                envelope["previous_version"], envelope["previous_chain"], record_hash,
                canonical(metadata).decode()))
        return dict(envelope, record_hash=record_hash)

    @staticmethod
    def decode(row):
        value = dict(row)
        value.pop("seq", None)
        value["metadata"] = strict_json(value["metadata"])
        return value

    def get(self, record_id):
        row = self.db.execute("SELECT * FROM records WHERE id=?", (record_id,)).fetchone()
        if row is None:
            raise AuditFailure("MISSING_EVIDENCE_REFERENCE")
        return self.decode(row)

    def records(self, kind=None, key=None):
        sql, args = "SELECT * FROM records WHERE 1=1", []
        for column, value in (("kind", kind), ("source_key", key)):
            if value is not None:
                sql += f" AND {column}=?"
                args.append(value)
        return [self.decode(r) for r in self.db.execute(sql + " ORDER BY seq", args)]

    def as_of(self, kind, key, cutoff):
        cutoff = timestamp(cutoff)
        matches = [r for r in self.records(kind, key) if timestamp(r["recorded_at"]) <= cutoff]
        return matches[-1] if matches else None

    def raw(self, record):
        sha = record["blob_sha"]
        if not sha:
            raise AuditFailure("MISSING_RAW_EVIDENCE")
        raw = (self.objects / sha).read_bytes()
        if digest(raw) != sha:
            raise AuditFailure("BLOB_HASH_MISMATCH")
        return raw

    def verify(self):
        previous, versions, count = None, {}, 0
        for record in self.records():
            expected = record.pop("record_hash")
            key = record["kind"], record["source_key"]
            if (record["previous_chain"] != previous
                    or record["previous_version"] != versions.get(key)
                    or digest(canonical(record)) != expected):
                raise AuditFailure("RECORD_CHAIN_MISMATCH")
            if record["blob_sha"]:
                self.raw(record)
            versions[key], previous = record["id"], expected
            count += 1
        return {"records": count, "head_hash": previous, "status": "VERIFIED"}
