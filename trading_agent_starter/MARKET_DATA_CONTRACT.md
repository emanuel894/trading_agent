# Phase A — multi-asset 30-minute historical data

This continues Foundation 0.2 on `feat/alpaca-paper-foundation`. The successful
Alpaca Paper read-only connection reported by the project owner is accepted as
the connectivity gate. No credentials or account calls are needed for the tests.

## Engineering decision

The architecture direction is sound. A trustworthy shared dataset is the next
milestone: both Quant-only and Quant+AI must eventually consume identical inputs.
There is no reason to rebuild the working broker layer or add agents now.

The existing `risk.py` and `ledger.py` are prototypes, not a connected execution
system. Their defaults (80% gross / 20% symbol) also differ from the proposed
baseline budget (60% / 10%, at most five positions). That does not block data
ingestion. Configure and test the experiment's budget in Phase B/C; complete
reconciliation, atomic risk reservations, loss limits and recovery before Phase D.

`HistoricalDataProvider` is separate from `BrokerAdapter`. A future IBKR data
provider can implement the same contract without changing the strategy engine.
The existing read-only adapter and its safety flags are preserved.

## Run on Windows

From the repository's `trading_agent_starter` directory, with the existing local
Paper `.env` and installed requirements:

```bat
.venv\Scripts\python.exe -m unittest discover -s tests -v
.venv\Scripts\python.exe -m agent alpaca-history --symbols SPY,QQQ --start 2026-09-01T00:00:00Z --end 2026-09-12T00:00:00Z --as-of 2026-09-12T00:00:00Z --output runs/history_spy_qqq_sep01_11
```

Then run the configured 12-symbol development universe by omitting `--symbols`:

```bat
.venv\Scripts\python.exe -m agent alpaca-history --config config/market_data.example.json --start 2026-09-01T00:00:00Z --end 2026-09-12T00:00:00Z --as-of 2026-09-12T00:00:00Z --output runs/history_universe_sep01_11
```

Choose a new output directory each time, or omit `--output` for a timestamped
directory. `--as-of` defaults to current UTC time; specify it for reproducibility.
Dates without an explicit timezone are rejected. Change the example symbols in
configuration as needed; they are a development fixture, not a recommendation or
a point-in-time historical universe. At most 20 symbols and 366 days per snapshot.

Outputs are `bars.csv` and `manifest.json`. Exit 0 and `DATA_CONTRACT_PASSED` mean
every expected eligible interval exists for every requested symbol. Exit 1 and
`DATA_CONTRACT_FAILED` mean gaps or no eligible bars; inspect the per-symbol
report before proceeding. Gap reports are still saved for diagnosis. A network,
malformed-data, or conflicting-duplicate error stops the command. No partial
successful dataset is published. Runtime data remains ignored by Git.

## Contract

| Field or rule | Meaning |
| --- | --- |
| `symbol` | Uppercase literal historical ticker; ordered deterministically |
| `timestamp` | UTC interval start, aligned to the regular session's 30-minute grid |
| `bar_end` | `timestamp + 30 minutes` |
| `available_at` | Bar end + configured assumed publication delay (default 60 seconds) |
| OHLC | Finite positive raw USD prices; low/high must bound open/close |
| Volume | Finite, nonnegative shares on the selected feed; zero is not fabricated |
| Window | Bar start >= start; bar end <= end; end <= as_of |
| Availability | `available_at <= as_of`; partial/unavailable bars excluded |
| Sessions | Alpaca calendar, including holidays and early closes; New York wall time converted to UTC with DST |
| Ordering | Timestamp, then symbol; identical duplicates collapsed and counted; conflicting duplicates rejected |
| Missing data | No forward filling, interpolation, symbol dropping, or synthetic zero-volume bars |
| Staleness | Latest expected interval missing per symbol, relative to the requested window; weekends/holidays are not false gaps |
| Persistence | CSV and manifest published together; existing snapshots not overwritten; CSV SHA-256 recorded |

The manifest includes the universe, feed, adjustment policy, session calendar,
requested cutoff, retrieval time, publication-delay assumption and quality report.
Downstream code must check `require_ready()` and use `visible_at(decision_time)`
for historical decision inputs. Never pass this intraday CSV to the legacy daily
`research --csv` command; the contracts are intentionally different.

## Provider details and scientific limits

- `alpaca-py==0.42.2` supplies `30Min` bars with explicit `feed=IEX`, raw prices,
  ascending order and `asof="-"` (no implicit historical ticker remapping).
  The SDK's bar `limit` is deliberately unset so its paginator reaches all
  symbols. Actual SDK pagination and response parsing are tested without HTTP.
  [Historical bars API](https://docs.alpaca.markets/us/reference/stockbars)
- The calendar's naive New York open/close timestamps are localized explicitly
  using the already installed `pytz` dependency, including on Windows. The pinned
  SDK documents calendar coverage from 1970 through 2029; requests beyond this
  range fail. The provider's calendar is the authoritative source for this slice.
  [Alpaca calendar](https://alpaca.markets/sdks/python/api_reference/trading/calendar.html)
- Historical downloads can contain subsequent vendor corrections. Neither
  `as_of` nor a publication delay proves historical publication time. The contract
  prevents unfinished/future intervals from entering earlier decisions; it is
  **not a point-in-time revision archive**. A later forward capture must record
  observed arrival times and corrections before stronger experimental claims.
- Raw prices avoid silently using future-adjusted history, but splits, dividends,
  delistings and symbol changes still need explicit handling before performance
  evaluation. A hand-picked current universe does not remove survivorship bias.
- IEX covers one exchange. Its volume does not measure consolidated liquidity;
  OHLCV cannot supply a bid/ask spread. Do not invent a spread filter from bar
  ranges. Phase B/C needs separate quote data or explicit execution assumptions.
  [Feed definitions](https://docs.alpaca.markets/us/reference/stockbars)
- A bar ending 14:00 with a 60-second delay is available at 14:01. A simulator
  cannot fill that decision at the already-passed 14:00 open. With only 30-minute
  bars, use a subsequent executable bar open (14:30 here), or obtain finer data.
- This is a bounded manual snapshot command. SDK retries are inherited; host
  supervision, request deadlines and reconnect policy remain prerequisites for
  the autonomous loop. No continuous runtime or trading execution is added.

## Acceptance evidence and next gate

Automated tests cover OHLCV validation, UTC normalization, strict completion and
publication cutoffs, future-input invariance, duplicate handling, missing symbols,
internal gaps and stale tails, holidays/weekends, early closes and DST, SDK
pagination across symbols (including empty intermediate pages and later-page
failure), Paper-only construction, CLI exit codes, hashes and failed-write cleanup.

The new workflow runs the suite and existing synthetic demo on Python 3.13 on
Ubuntu and Windows. Local results and remote CI state are reported separately in
the PR; workflow creation alone is not evidence that Windows has passed.

The remaining real-data gate is to run the two commands above on the already
connected Windows machine and inspect the resulting manifests. No real historical
download or profitability result is claimed by this implementation.

After that: Phase B, a frozen EMA20/EMA60 + EMA100 regime + ATR14 baseline using
this contract, explicit warmup/HOLD behavior and the proposed deterministic
portfolio limits. Then Phase C's multi-asset simulator with valid fill timing and
costs. Paper orders, the autonomous loop and AI remain later gates.
