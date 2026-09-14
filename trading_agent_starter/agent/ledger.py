"""Durable local intent deduplication and stop latch. No broker exactly-once claim."""
import json
import sqlite3
from pathlib import Path


class Ledger:
    def __init__(self, path: str):
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path, timeout=10)
        self.db.execute("PRAGMA journal_mode=WAL")
        self.db.execute("PRAGMA synchronous=FULL")
        self.db.executescript("""
        CREATE TABLE IF NOT EXISTS intents (
            intent_id TEXT PRIMARY KEY, payload TEXT NOT NULL, status TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS control (key TEXT PRIMARY KEY, value TEXT NOT NULL);
        """)

    def reserve(self, intent_id: str, payload: dict) -> bool:
        data = json.dumps(payload, sort_keys=True, allow_nan=False)
        with self.db:
            row = self.db.execute("SELECT payload FROM intents WHERE intent_id=?", (intent_id,)).fetchone()
            if row:
                if row[0] != data:
                    raise ValueError("Intent ID reused with changed payload.")
                return False
            try:
                self.db.execute("INSERT INTO intents VALUES (?, ?, 'RESERVED')", (intent_id, data))
            except sqlite3.IntegrityError:
                # Another process won the reservation: never submit twice.
                return False
        return True

    def halt(self, reason: str) -> None:
        with self.db:
            self.db.execute("INSERT OR REPLACE INTO control VALUES ('halt', ?)", (reason,))

    @property
    def halted(self) -> bool:
        return self.db.execute("SELECT 1 FROM control WHERE key='halt'").fetchone() is not None

    def close(self) -> None:
        self.db.close()
