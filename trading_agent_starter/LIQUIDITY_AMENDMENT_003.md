# ADR001-LIQUIDITY-003 — provider-native daily liquidity input

Status: registered before replacement cohort construction or performance access.
This amendment changes only the liquidity data definition. Amendment 002, its
registration, selector, scope registry, evidence and reviews remain byte-identical.
The prior RTH definition is reproducible using `agent.cohort_selector` and
registration 002. It must not be passed off as the amended provider-native input.

The replacement selection registration is
`research/cohort_selection_registration_003.json`, SHA-256
`af7e721326576b0e6b131debd1b5f8665c474adc2472ab75d483fb654f35eed2`.
`research/cohort_liquidity_amendment_003.json` records the amendment and hashes of
the unchanged prior artifacts. No population research or issuer selection was
used to choose this definition.

The metric is exactly:

`median(previous 60 session-date Alpaca SIP 1Day raw close × Alpaca SIP 1Day raw volume)`

Requests must explicitly use `timeframe=1Day`, `feed=sip`, `adjustment=raw`,
`asof=-`. The preceding session's same provider-native daily close must be at
least $10. The $20m median threshold, exact 60 preceding session dates, monthly
cutoff/ranking, most liquid eligible class, top-500 rule, dated common-share
eligibility, calendar-2025 window and subsequent 25-issuer/two-filing selection
are unchanged. Missing data remains UNRESOLVED; older bars cannot fill a gap.

Alpaca groups daily bars by New York calendar day and timestamps the left edge
at local midnight (UTC offset follows DST). Daily volume can include trades
that do not update daily prices, including extended-hours conditions. This is
a **provider-native liquidity proxy**, not RTH-only volume, official
closing-price dollar volume, or actual traded dollar notional. Session dates
come from the registered market calendar; the entire daily bucket must have
completed before the monthly cutoff. Historical retrieval is not proof of an
unrevised vendor vintage available at that historical cutoff.

Definitions: [Alpaca Market Data FAQ](https://docs.alpaca.markets/us/docs/market-data-faq)
and [Historical bars API](https://docs.alpaca.markets/us/reference/stockbars),
reviewed 2026-09-21. `asof=-` disables automatic rename mapping; dated
instrument/class/ticker evidence is still required for every session date.

## Versioned input contract

`agent.cohort_selector_v3` accepts only `adr001-universe-inputs-v2` bundles with
`liquidity_definition_version=alpaca-sip-1day-ny-calendar-v1`. The original
bundle fields remain, with that version field added. Every bar retains the old
date, instrument ID, ticker, close, volume and evidence references, and requires:

| Field | Exact value |
|---|---|
| `provider` | `alpaca` |
| `timeframe` | `1Day` |
| `feed` | `sip` |
| `adjustment` | `raw` |
| `asof` | `-` |
| `session` | `PROVIDER_NATIVE_NY_CALENDAR_DAY` |
| `liquidity_definition_version` | `alpaca-sip-1day-ny-calendar-v1` |
| `timestamp` | Provider timestamp at New York midnight, matching `date` |

No RTH alias or implicit conversion is accepted. The selector reuses amendment
002's identity, calendar, ranking and event-selection helpers. Future scope
verification binds the registration, liquidity version, exact input bars,
provider contract and both selector/helper code hashes. A version change
requires an explicit amendment and invalidates that scope and scoped reviews.
The new module exposes preparation/verification functions only: it does not
write a cohort or enable the old v2 freeze CLI for v3. Future authorized freeze
integration must use v3 verification; the unchanged v2 registry is replay history.

## Bounded local smoke test

From `trading_agent_starter`, using the existing `.venv` and local `.env`:

```powershell
.\.venv\Scripts\python.exe -m agent.daily_liquidity_probe --store runs/daily_liquidity_smoke
```

The command requests only AAPL and SPY for January 13–15, 2025: six expected
daily bars. There are no symbol/window overrides. Limits are three pages, five
HTTP attempts including retries, 64 KiB per response and 192 KiB total response
budget. Only the existing read-only market-data GET transport is used.
Existing credential environment names and `.env` loading are reused; credential
values and authentication headers are neither printed nor stored.

The report separates authenticated historical SIP access from data quality.
It checks all symbol counts, exact dates, local-midnight timestamps, finite
positive OHLCV, OHLC consistency and integer volume. Explicit request parameters
establish the API contract; responses do not echo all four parameters, so the
report does not claim independent provider-side attestation. Raw responses,
request URLs, response statuses/timing and hashes are preserved in the immutable
evidence store; each report gets a new filename. Invalid data cannot relabel
successful access as NOT_ENTITLED. Exit 0 requires complete valid data for both
symbols; incomplete/invalid/restricted results exit 2. No IEX fallback exists.

This milestone runs synthetic local/CI tests, not the account smoke test.
Actual account results must come from the owner's local invocation. It does
not construct/freeze a cohort, acquire a universe, change the 30-minute
pipeline, or run any trading/research evaluation.
