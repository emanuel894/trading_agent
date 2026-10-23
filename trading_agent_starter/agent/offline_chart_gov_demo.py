"""Issue #34: fixed synthetic facts, never signals or source acquisition.

Run from trading_agent_starter (no credentials/network/dependencies):
  python -m agent.offline_chart_gov_demo --output runs/issue34
  python -m agent.offline_chart_gov_demo --output runs/issue34-measured --benchmark

This local fixture adapter illustrates Issue #12 envelope concepts; it is NOT
an admitted source, schema implementation, strategy, or scientific registration.
Stdlib statistics/difflib/Decimal are reused. No optional indicator package is
required or benchmarked; no general charting/backtesting engine is introduced.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import difflib
import hashlib
import json
import math
from pathlib import Path
import platform
import re
import statistics
import time
import tracemalloc


START = datetime(2026, 1, 1, 16, tzinfo=timezone.utc)
CONVENTIONS = {
    "source": "fixed synthetic instrument SYNTHETIC_ONLY; no real source",
    "calendar": "invented daily UTC sessions, including weekends; not an exchange calendar",
    "bar": "one synthetic session ending 16:00 UTC; OHLC in synthetic price units",
    "adjustment": "raw synthetic prices; no corporate actions or total-return adjustment",
    "volume": "synthetic units, not liquidity evidence; null is unknown, zero is observed zero",
    "cutoff": "all required clocks strictly before cutoff; equal timestamps abstain",
    "sma": "arithmetic close mean over 3/5 consecutive scheduled sessions; full warmup",
    "volatility_3": "population stddev (ddof=0) of 3 adjacent close fractional changes; 4 bars; not annualized",
    "range_3": "max(high)-min(low) over current and previous 2 scheduled sessions",
    "breakout": "close minus max(high) of previous 3 scheduled sessions, excluding current",
    "volume_features": "volume/previous_volume-1; volume/mean(previous 3 volumes); zero denominator => null",
    "missingness": "no interpolation/fill; windows crossing missing/unavailable sessions abstain",
    "lineage": "each row lists up to 5 selected input versions; hashes bind complete snapshot",
    "chart": "fixed price axis 90..120, one column per price unit; clipped values marked !",
    "statement_spans": "half-open UTF-8 byte offsets into retained text, bound to raw SHA-256",
}


def _aware(value):
    if not isinstance(value, datetime) or value.utcoffset() is None:
        raise ValueError("An explicit timezone-aware timestamp is required")
    return value


def _stamp(value):
    return _aware(value).astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _hash(value):
    return hashlib.sha256(value).hexdigest()


def _json(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + "\n"


@dataclass(frozen=True, slots=True)
class Clocks:
    published: datetime | None
    observed: datetime | None
    received: datetime | None
    ingested: datetime | None
    verified: datetime | None
    revised: datetime | None = None

    def available_before(self, cutoff):
        _aware(cutoff)
        required = (self.published, self.observed, self.received, self.ingested, self.verified)
        if any(t is None for t in required):
            return False
        known = tuple(_aware(t) for t in required)
        if tuple(sorted(known)) != known:
            return False  # conflicting clocks remain unavailable
        if self.revised is not None:
            known += (_aware(self.revised),)
        return max(known) < cutoff


def _clocks(published, revised=None):
    return Clocks(published, published + timedelta(seconds=1),
                  published + timedelta(seconds=2), published + timedelta(seconds=3),
                  published + timedelta(seconds=4), revised)


@dataclass(frozen=True, slots=True)
class Bar:
    evidence_id: str
    end: datetime
    open: float
    high: float
    low: float
    close: float
    volume: float | None
    clocks: Clocks
    previous_version: str | None = None


def chart_fixture(size=24):
    """Flat/trend/spike/oscillation, absent sessions 6/10/11, null volume and correction."""
    sessions = tuple(START + timedelta(days=i) for i in range(size))
    prices = (100, 100, 100, 102, 104, 108, 107, 106, 109, 103, 104, 105,
              110, 98, 112, 101, 108, 106, 105, 104, 106, 108, 107, 109)
    bars = []
    for i, end in enumerate(sessions):
        if i in (6, 10, 11):
            continue
        close = prices[i % len(prices)]
        bars.append(Bar(f"synthetic:bar:{i}:r1", end, close, close + 1, close - 1,
                        close, None if i == 9 else (300 if i == 5 else 100),
                        _clocks(end + timedelta(seconds=1))))
    if size > 15:
        original = next(b for b in bars if b.evidence_id == "synthetic:bar:4:r1")
        revised = sessions[15] + timedelta(seconds=1)
        bars.append(replace(original, evidence_id="synthetic:bar:4:r2", close=103, low=102,
                            previous_version=original.evidence_id,
                            clocks=_clocks(revised, revised=revised)))
    return sessions, tuple(bars)


def _select(records, cutoff, group):
    """Select observed versions without mutating originals; fixture-local only."""
    _aware(cutoff)
    by_id = {r.evidence_id: r for r in records}
    if len(by_id) != len(records):
        raise ValueError("Duplicate evidence version")
    selected = {}
    for record in records:
        if record.previous_version is not None:
            previous = by_id.get(record.previous_version)
            if previous is None or group(previous) != group(record):
                raise ValueError("Revision requires its original same-event version")
            if record.clocks.revised is None:
                continue
        if not record.clocks.available_before(cutoff):
            continue
        key = group(record)
        prior = selected.get(key)
        if prior is not None and prior.clocks.verified == record.clocks.verified:
            raise ValueError("Ambiguous same-time versions")
        if prior is None or prior.clocks.verified < record.clocks.verified:
            selected[key] = record
    return selected


def chart_snapshot(sessions, bars, cutoff):
    _aware(cutoff)
    if tuple(sorted(set(sessions))) != tuple(sessions):
        raise ValueError("Sessions must be unique and ordered")
    for end in sessions:
        _aware(end)
    session_set = set(sessions)
    for bar in bars:
        _aware(bar.end)
        values = (bar.open, bar.high, bar.low, bar.close)
        if (bar.end not in session_set or not all(math.isfinite(v) and v > 0 for v in values)
                or not bar.low <= min(bar.open, bar.close) <= max(bar.open, bar.close) <= bar.high
                or (bar.volume is not None and (not math.isfinite(bar.volume) or bar.volume < 0))):
            raise ValueError("Invalid synthetic OHLCV")
    selected = _select(bars, cutoff, lambda b: b.end)
    visible = [selected.get(end) if end < cutoff else None for end in sessions]
    rows = []
    for i, end in enumerate(sessions):
        if end >= cutoff:
            break
        bar = visible[i]
        window = visible[max(0, i - 4):i + 1]

        def trailing(length, lag=0):
            stop = i + 1 - lag
            start = stop - length
            values = visible[start:stop] if start >= 0 else []
            return values if len(values) == length and all(v is not None for v in values) else None

        row = {"end": _stamp(end), "status": "available" if bar else "missing_or_unavailable",
               "evidence_id": bar.evidence_id if bar else None,
               "close": bar.close if bar else None,
               "input_versions": [b.evidence_id if b else None for b in window],
               "sma_3": None, "sma_5": None, "volatility_3": None, "range_3": None,
               "breakout_distance_3": None, "breakout": "unavailable",
               "volume_change": None, "volume_ratio_3": None}
        for length in (3, 5):
            values = trailing(length)
            if values:
                row[f"sma_{length}"] = statistics.fmean(b.close for b in values)
        values = trailing(4)
        if values:
            row["volatility_3"] = statistics.pstdev(
                b.close / a.close - 1 for a, b in zip(values, values[1:]))
        values = trailing(3)
        if values:
            row["range_3"] = max(b.high for b in values) - min(b.low for b in values)
        prior = trailing(3, lag=1)
        if bar and prior:
            distance = bar.close - max(b.high for b in prior)
            row["breakout_distance_3"] = distance
            row["breakout"] = "above_prior_high" if distance > 0 else "at_or_below_prior_high"
            if bar.volume is not None and all(b.volume is not None for b in prior):
                baseline = statistics.fmean(b.volume for b in prior)
                if baseline > 0:
                    row["volume_ratio_3"] = bar.volume / baseline
        previous = trailing(2)
        if previous and bar.volume is not None and previous[0].volume not in (None, 0):
            row["volume_change"] = bar.volume / previous[0].volume - 1
        rows.append(row)
    lineage = [{**asdict(b), "end": _stamp(b.end),
                "clocks": {k: _stamp(v) if v else None for k, v in asdict(b.clocks).items()}}
               for b in selected.values() if b.end < cutoff]
    lineage.sort(key=lambda b: (b["end"], b["evidence_id"]))
    return {"cutoff": _stamp(cutoff), "rows": rows, "selected_inputs": lineage}


def chart_view(snapshot):
    lines = ["SYNTHETIC ONLY | fixed axis 90..120 | * close, + SMA3, @ overlap"]
    for row in snapshot["rows"]:
        cells = [" "] * 31
        for field, marker in (("sma_3", "+"), ("close", "*")):
            value = row[field]
            if value is not None:
                column = max(0, min(30, round(value) - 90))
                cells[column] = "!" if not 90 <= value <= 120 else (
                    "@" if cells[column] != " " else marker)
        lines.append(f"{row['end'][:10]} |{''.join(cells)}| {row['close']}")
    return "\n".join(lines) + "\n"


@dataclass(frozen=True, slots=True)
class Statement:
    evidence_id: str
    event_id: str
    text: str
    effective: datetime
    clocks: Clocks
    previous_version: str | None = None


def statement_fixture():
    first = START + timedelta(hours=2)
    second = first + timedelta(days=7)
    correction = second + timedelta(hours=2)
    return (
        Statement("synthetic:fomc:A:r1", "synthetic:fomc:A",
                  "SYNTHETIC FOMC-style statement A.\nTarget range: 4.50 to 4.75 percent.\nInflation remains elevated.",
                  first + timedelta(days=1), _clocks(first)),
        Statement("synthetic:fomc:B:r1", "synthetic:fomc:B",
                  "SYNTHETIC FOMC-style statement B.\nTarget range: 4.25 to 4.50 percent.\nInflation has eased.",
                  second + timedelta(days=1), _clocks(second)),
        Statement("synthetic:fomc:B:r2", "synthetic:fomc:B",
                  "SYNTHETIC FOMC-style statement B.\nTarget range: 4.00 to 4.25 percent.\nInflation has eased.\nCorrected numeric range.",
                  second + timedelta(days=1), _clocks(correction, revised=correction),
                  "synthetic:fomc:B:r1"),
    )


def _statement_record(statement):
    text = statement.text
    digest = _hash(text.encode("utf-8"))

    def span(start, end):
        return {"byte_span": [len(text[:start].encode("utf-8")), len(text[:end].encode("utf-8"))],
                "artifact_sha256": digest}

    matches = list(re.finditer(r"Target range: (\d+\.\d{2}) to (\d+\.\d{2}) percent\.", text))
    facts = []
    if len(matches) == 1:
        match = matches[0]
        for index, label in ((1, "lower"), (2, "upper")):
            facts.append({"measure": label, "value": match.group(index),
                          "unit": "percent", **span(*match.span(index))})
    terms = {term: [{"text": m.group(), **span(*m.span())}
                    for m in re.finditer(r"\b" + term + r"\b", text, re.IGNORECASE)]
             for term in ("elevated", "eased", "corrected")}
    return {"evidence_id": statement.evidence_id, "event_id": statement.event_id,
            "previous_version": statement.previous_version, "text": text, "raw_sha256": digest,
            "capture_mode": "fixture", "source": "synthetic official-release example, not Fed text",
            "economic_effective": _stamp(statement.effective),
            "clocks": {k: _stamp(v) if v else None for k, v in asdict(statement.clocks).items()},
            "rate_status": "available" if facts else "unavailable", "rate_facts": facts,
            "terms": terms, "model": None}


def _rate_difference(new, old):
    if not new or not old or not new["rate_facts"] or not old["rate_facts"]:
        return None
    return [str(Decimal(n["value"]) - Decimal(o["value"]))
            for n, o in zip(new["rate_facts"], old["rate_facts"])]


def statement_snapshot(versions, cutoff):
    selected = _select(versions, cutoff, lambda s: s.event_id)
    ordered = sorted(selected.values(), key=lambda s: s.effective)
    available = sorted((v for v in versions if v.clocks.available_before(cutoff)
                        and (v.previous_version is None or v.clocks.revised is not None)),
                       key=lambda s: s.clocks.verified)
    records = [_statement_record(s) for s in available]
    current = _statement_record(ordered[-1]) if ordered else None
    prior = _statement_record(ordered[-2]) if len(ordered) > 1 else None
    original = next((r for r in records if current and
                     r["evidence_id"] == current["previous_version"]), None)
    def text_difference(old):
        return "\n".join(difflib.unified_diff(
            old["text"].splitlines(), current["text"].splitlines(),
            fromfile=old["evidence_id"], tofile=current["evidence_id"], lineterm="")) if old and current else ""

    return {"cutoff": _stamp(cutoff), "versions": records, "selected": current,
            "rate_change_pp": _rate_difference(current, prior),
            "revision_change_pp": _rate_difference(current, original),
            "text_diff": text_difference(prior), "revision_text_diff": text_difference(original)}


def benchmark(sizes=(10_000, 100_000), repetitions=5):
    """Warm full chart snapshot; timings exclude generation/tracing; memory includes both."""
    cases = []
    for size in sizes:
        sessions, bars = chart_fixture(size)
        cutoff = sessions[-1] + timedelta(seconds=10)
        chart_snapshot(sessions, bars, cutoff)  # warm-up, not timed
        durations = []
        for _ in range(repetitions):
            start = time.perf_counter()
            chart_snapshot(sessions, bars, cutoff)
            durations.append(time.perf_counter() - start)
        del sessions, bars
        tracemalloc.start()
        try:
            sessions, bars = chart_fixture(size)
            chart_snapshot(sessions, bars, sessions[-1] + timedelta(seconds=10))
            peak = tracemalloc.get_traced_memory()[1]
        finally:
            tracemalloc.stop()
        ordered = sorted(durations)
        cases.append({"rows": size, "p50_seconds": statistics.median(durations),
                      "p95_seconds": ordered[math.ceil(0.95 * repetitions) - 1],
                      "peak_tracemalloc_bytes": peak})
    return {"cases": cases, "repetitions": repetitions, "python": platform.python_version(),
            "platform": platform.platform(), "processor": platform.processor() or "unavailable",
            "method": "5 warm samples by default; nearest-rank p95; no cold timing; tracemalloc not RSS; fixture+snapshot peak",
            "scope": "single-process synthetic chart pipeline, no renderer/statement benchmark or speed comparison"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, help="new output directory; existing paths refused")
    parser.add_argument("--benchmark", action="store_true")
    args = parser.parse_args()
    output = Path(args.output)
    output.mkdir(parents=True, exist_ok=False)
    sessions, bars = chart_fixture()
    statements = statement_fixture()
    early = sessions[5] + timedelta(seconds=10)
    late = sessions[-1] + timedelta(seconds=10)
    statement_cutoff = statements[1].clocks.verified + timedelta(seconds=1)
    chart = chart_snapshot(sessions, bars, early)
    statement = statement_snapshot(statements, statement_cutoff)
    packet = {"scope": "SYNTHETIC_OFFLINE_ONLY", "model_calls": 0, "external_spend_usd": 0,
              "conventions": CONVENTIONS, "chart_frozen": chart,
              "chart_later": chart_snapshot(sessions, bars, late),
              "statement_frozen": statement, "statement_later": statement_snapshot(statements, late),
              "adopt_vs_build": "ADOPT stdlib statistics, Decimal, difflib; KEEP_OURS fixture adapter only; optional indicator libraries unmeasured; screenshot AI/LLM DEFERRED",
              "limits": "Not source/schema qualification, real market calendar, prediction, backtest, latency or alpha evidence. No model/provider/broker calls."}
    packet["frozen_sha256"] = {"chart": _hash(_json(chart).encode("utf-8")),
                               "statement": _hash(_json(statement).encode("utf-8"))}
    (output / "snapshot.json").write_text(_json(packet), encoding="utf-8", newline="\n")
    (output / "chart.txt").write_text(chart_view(chart), encoding="utf-8", newline="\n")
    if args.benchmark:
        (output / "benchmark.json").write_text(_json(benchmark()), encoding="utf-8", newline="\n")
    print(f"SYNTHETIC_OFFLINE_ONLY: {output}; no predictions or alpha claim")


if __name__ == "__main__":
    main()
