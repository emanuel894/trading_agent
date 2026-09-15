"""Provider-independent, regular-session 30-minute OHLCV contract.

Historical snapshots are NOT point-in-time vendor archives. `available_at` is
an explicit simulation assumption, not proof of when a revised bar arrived.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import hashlib
import io
import json
import math
from pathlib import Path
import re
import shutil
import tempfile
from typing import Iterable, Protocol

INTERVAL = timedelta(minutes=30)
SCHEMA_VERSION = "ohlcv-30m-v1"


def utc(value: datetime) -> datetime:
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("An explicit timezone is required for every timestamp")
    return value.astimezone(timezone.utc)


def iso(value: datetime) -> str:
    return utc(value).isoformat().replace("+00:00", "Z")


def symbols_from(values: Iterable[str]) -> tuple[str, ...]:
    if isinstance(values, str):
        raise ValueError("Supply symbols as a sequence, not a single string")
    normalized = tuple(sorted(set(value.strip().upper() for value in values)))
    if not 1 <= len(normalized) <= 20 or any(
        not re.fullmatch(r"[A-Z][A-Z0-9.\-]{0,14}", s) for s in normalized
    ):
        raise ValueError("Supply 1–20 nonempty U.S. equity/ETF symbols")
    return normalized


@dataclass(frozen=True)
class HistoryRequest:
    symbols: tuple[str, ...]
    start: datetime
    end: datetime  # exclusive bar interval boundary
    as_of: datetime  # decision cutoff, independent of download time
    publication_delay_seconds: int = 60

    def __post_init__(self):
        object.__setattr__(self, "symbols", symbols_from(self.symbols))
        for name in ("start", "end", "as_of"):
            object.__setattr__(self, name, utc(getattr(self, name)))
        if not self.start < self.end <= self.as_of:
            raise ValueError("Require start < end <= as_of")
        if self.end - self.start > timedelta(days=366):
            raise ValueError("Fetch at most 366 days per snapshot")
        if type(self.publication_delay_seconds) is not int or not 0 <= self.publication_delay_seconds <= 3600:
            raise ValueError("Publication delay must be an integer from 0 to 3600 seconds")

    @property
    def delay(self) -> timedelta:
        return timedelta(seconds=self.publication_delay_seconds)


@dataclass(frozen=True)
class Session:
    open: datetime
    close: datetime

    def __post_init__(self):
        object.__setattr__(self, "open", utc(self.open))
        object.__setattr__(self, "close", utc(self.close))
        duration = self.close - self.open
        if (duration <= timedelta(0) or duration > timedelta(hours=6, minutes=30)
                or duration % INTERVAL or self.open.date() != self.close.date()):
            raise ValueError("Invalid regular-session calendar interval")


@dataclass(frozen=True)
class RawBar:
    symbol: str
    timestamp: datetime  # interval START; values checked only after time filtering
    open: float
    high: float
    low: float
    close: float
    volume: float


@dataclass(frozen=True)
class Bar30m:
    symbol: str
    timestamp: datetime
    available_at: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float

    @property
    def end(self) -> datetime:
        return self.timestamp + INTERVAL


@dataclass(frozen=True)
class HistorySnapshot:
    request: HistoryRequest
    sessions: tuple[Session, ...]
    bars: tuple[Bar30m, ...]
    expected: tuple[datetime, ...]
    missing: tuple[tuple[str, tuple[datetime, ...]], ...]
    excluded: tuple[tuple[str, int], ...]
    source: str
    feed: str
    adjustment: str
    symbol_mapping: str

    @property
    def ready(self) -> bool:
        return bool(self.expected) and not any(times for _, times in self.missing)

    def require_ready(self) -> None:
        if not self.ready:
            raise ValueError("Historical data gate failed: no eligible bars or missing intervals")

    def visible_at(self, decision_time: datetime) -> tuple[Bar30m, ...]:
        """A future baseline must request its inputs through this time boundary."""
        decision_time = utc(decision_time)
        if decision_time > self.request.as_of:
            raise ValueError("Decision time exceeds snapshot cutoff")
        return tuple(bar for bar in self.bars if bar.available_at <= decision_time)

    def quality(self) -> dict:
        expected_latest = self.expected[-1] if self.expected else None
        return {
            "status": "DATA_CONTRACT_PASSED" if self.ready else "DATA_CONTRACT_FAILED",
            "expected_bars_per_symbol": len(self.expected),
            "expected_latest_bar_start": iso(expected_latest) if expected_latest else None,
            "excluded_rows": dict(self.excluded),
            "symbols": {
                symbol: {
                    "bars": len(self.expected) - len(missing),
                    "missing_intervals": [iso(t) for t in missing],
                    # Relative to the requested window, never today's wall clock.
                    "stale": expected_latest is not None and expected_latest in missing,
                }
                for symbol, missing in self.missing
            },
        }


class HistoricalDataProvider(Protocol):
    def fetch(self, request: HistoryRequest) -> HistorySnapshot: ...


def normalize_bars(
    request: HistoryRequest, sessions: Iterable[Session], rows: Iterable[RawBar], *,
    source: str, feed: str, adjustment: str = "raw", symbol_mapping: str = "literal",
) -> HistorySnapshot:
    if adjustment != "raw" or symbol_mapping != "literal":
        raise ValueError("This contract requires raw prices and literal historical symbols")
    ordered_sessions = tuple(sorted(sessions, key=lambda s: s.open))
    calendar = {}
    expected = []
    for session in ordered_sessions:
        day = session.open.date()
        if day in calendar or not request.start.date() <= day <= request.end.date():
            raise ValueError("Duplicate or out-of-range calendar session")
        calendar[day] = session
        stamp = session.open
        while stamp + INTERVAL <= session.close:
            if (stamp >= request.start and stamp + INTERVAL <= request.end
                    and stamp + INTERVAL + request.delay <= request.as_of):
                expected.append(stamp)
            stamp += INTERVAL
    expected_set = set(expected)
    bars = {}
    excluded = {"outside_window": 0, "outside_session": 0, "not_available": 0, "identical_duplicate": 0}
    for row in rows:
        symbol = row.symbol.strip().upper()
        if symbol not in request.symbols:
            raise ValueError("Provider returned an unrequested symbol")
        stamp = utc(row.timestamp)
        if stamp < request.start or stamp >= request.end:
            excluded["outside_window"] += 1
            continue
        session = calendar.get(stamp.date())
        if session is None or not session.open <= stamp < session.close:
            excluded["outside_session"] += 1
            continue
        if (stamp - session.open) % INTERVAL:
            raise ValueError(f"Misaligned 30-minute timestamp for {symbol}: {iso(stamp)}")
        if stamp not in expected_set:
            excluded["not_available"] += 1
            continue
        values = tuple(float(getattr(row, k)) for k in ("open", "high", "low", "close", "volume"))
        o, h, low, c, v = values
        if (not all(math.isfinite(x) for x in values) or min(o, h, low, c) <= 0
                or v < 0 or low > min(o, c) or h < max(o, c)):
            raise ValueError(f"Invalid OHLCV for {symbol}: {iso(stamp)}")
        bar = Bar30m(symbol, stamp, stamp + INTERVAL + request.delay, *values)
        key = (stamp, symbol)
        if key in bars:
            if bars[key] != bar:
                raise ValueError(f"Conflicting duplicate for {symbol}: {iso(stamp)}")
            excluded["identical_duplicate"] += 1
        else:
            bars[key] = bar
    missing = tuple((s, tuple(t for t in expected if (t, s) not in bars)) for s in request.symbols)
    return HistorySnapshot(request, ordered_sessions, tuple(bars[k] for k in sorted(bars)),
                           tuple(expected), missing, tuple(sorted(excluded.items())),
                           source, feed, adjustment, symbol_mapping)


def write_snapshot(snapshot: HistorySnapshot, output: Path, *, retrieved_at: datetime) -> dict:
    """Publish CSV + manifest together; existing output directories are never reused."""
    retrieved_at = utc(retrieved_at)
    if retrieved_at < snapshot.request.as_of:
        raise ValueError("Snapshot cutoff cannot be in the future at retrieval")
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer, lineterminator="\n")
    writer.writerow(("symbol", "timestamp", "bar_end", "available_at", "open", "high", "low", "close", "volume"))
    for b in snapshot.bars:
        writer.writerow((b.symbol, iso(b.timestamp), iso(b.end), iso(b.available_at),
                         b.open, b.high, b.low, b.close, b.volume))
    payload = buffer.getvalue().encode("utf-8")
    request = snapshot.request
    manifest = {
        "schema_version": SCHEMA_VERSION,
        "source": snapshot.source, "feed": snapshot.feed, "currency": "USD",
        "adjustment": snapshot.adjustment, "symbol_mapping": snapshot.symbol_mapping,
        "timeframe": "30Min", "timestamp_semantics": "interval_start_utc",
        "session": "regular", "calendar_timezone": "America/New_York",
        "start_inclusive": iso(request.start), "end_exclusive": iso(request.end),
        "as_of": iso(request.as_of), "retrieved_at": iso(retrieved_at),
        "publication_delay_seconds": request.publication_delay_seconds,
        "symbols": list(request.symbols),
        "sessions": [{"open": iso(s.open), "close": iso(s.close)} for s in snapshot.sessions],
        "bars_file": "bars.csv", "bars_sha256": hashlib.sha256(payload).hexdigest(),
        "quality": snapshot.quality(),
        "limitations": [
            "Historical vendor snapshot; not a point-in-time revision archive.",
            "available_at is bar end plus assumed delay, not observed publication time.",
            "Static example universe; no survivorship-free or total-return claim.",
            "Raw prices; corporate actions need handling before strategy evaluation.",
            "IEX is a single exchange; OHLCV contains no spread or consolidated liquidity.",
        ],
    }
    output = Path(output)
    if output.exists():
        raise ValueError("Output already exists; choose a new snapshot directory")
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".history-", dir=output.parent))
    try:
        (staging / "bars.csv").write_bytes(payload)
        (staging / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return manifest
