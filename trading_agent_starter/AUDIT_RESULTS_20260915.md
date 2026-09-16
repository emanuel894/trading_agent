# 10-Q audit implementation and measured probes — 2026-09-15

**Outcome: acquisition gate NOT PASSED.** The bounded read-only audit is implemented.
Real SEC acquisition worked for Apple and Microsoft. Three target filings were
attempted; two completed document/comparator/prior-disclosure processing. No
target was eligible. The required 50-filing/25-issuer audit has **not** been run.

`REALTIME_SIP = NOT_ENTITLED`

## Measured acquisition and provenance

| Probe | Actual acquisition | Result |
|---|---|---|
| Initial Apple probe | 30 HTTP responses, all 200; two current 10-Qs downloaded/parsed. One full comparison and 20-document prior inventory completed. | The second target's prior acquisition hit the registered 30-request cap. The same run did not reach Microsoft. All failures were retained. |
| Separate Microsoft probe | 15 HTTP responses, all 200; one current 10-Q, prior fiscal comparator and 20-document prior inventory completed. | Document stages completed; instrument mapping and prior-disclosure review remained unavailable. |
| SEC timestamp cross-check | Revalidated 17 distinct saved Apple submissions offline against accession, issuer, form and New York-header/UTC-API acceptance agreement. Microsoft downloads enforced that check directly. | Passed for those records. This establishes consistent SEC metadata, not earliest issuer publication. |
| Immutable-store verification | Apple: 142 records; Microsoft: 81 records at preservation. Raw blobs, record hashes, prior-version links and record chains checked. | Passed. The later Apple verification records append to, rather than overwrite, the initial report's evidence. |
| SIP / execution context | Owner's credentialed Windows probe observed historical SIP 1-minute bars HTTP 200 with AAPL/SPY rows; seven HTTP 200 paginated SIP quote responses; at least 13,088 AAPL quote rows; no auth/subscription/permission/entitlement error. | Historical SIP provider access is observed. The initial probe incorrectly failed during quote-quality validation; the corrected probe separates entitlement from quality. Real-time remains `REALTIME_SIP = NOT_ENTITLED`. |

## Independent historical SIP entitlement probe

The standalone probe was added and unit-tested without importing the full 10-Q
audit context. It is limited to two GET-only endpoint calls (AAPL/SPY `1Min`
bars and quotes, identical completed window; any explicit pagination is
retained), hard-requires `feed=sip`, and records raw
responses plus request receipt/status/elapsed metadata in the append-only store.
It does not use IEX, the validated 30-minute pipeline, status/security-master
inputs, forecasting, LLMs, allocation or orders.

The local execution environment used for this implementation has no Alpaca
credentials, so its run stopped before network access with
`CREDENTIALS_UNAVAILABLE`; this is separate from the owner's credentialed
Windows result above. Rerun the single Windows probe command in the README on
the credentialed machine to obtain the corrected immutable report and its
`SUCCEEDED_WITH_ROWS`, `SUCCEEDED_EMPTY`, `DELAYED_LIMITED` or provider
restriction classification. No subscription was purchased or recommended.
The separately supplied real-time result remains `REALTIME_SIP = NOT_ENTITLED`.

The observed account result exposed a probe bug: seven HTTP 200 SIP quote pages
and at least 13,088 AAPL rows were incorrectly turned into `FAILED` by the
execution-quality check `INVALID_HISTORICAL_QUOTE`; SPY was shown as zero only
because processing stopped before its count was recorded. The corrected probe
now counts both symbols first, classifies entitlement only from authenticated
200/SIP/structured responses and row coverage, and places quote conditions,
crossed/locked/zero-size counts, malformed rows and strict-policy pass counts
under a separate `data_quality` section. A quote-quality failure can no longer
label successful historical SIP access as `NOT_ENTITLED`.

Targets: Apple `0000320193-25-000008` (completed) and
`0000320193-25-000057` (partial); Microsoft `0000950170-25-010491` (completed).
These are a convenience acquisition probe, not a historical investable universe.

## Measured latency — individual observations, not population estimates

| Stage, seconds | Completed Apple target | Completed Microsoft target |
|---|---:|---:|
| Current filing acquisition | 11.00 | 12.68 |
| Current MD&A parsing | 0.12 | 0.80 |
| Prior-document acquisition | 143.81 | 143.47 |
| Prior comparable parsing | 0.10 | 0.76 |
| Other prior-disclosure parsing | 0.80 | 4.14 |
| Deterministic paragraph linkage | 1.34 | 5.46 |
| Total per-target audit | 157.15 | 167.31 |

These are local wall/monotonic acquisition measurements on backfilled documents;
they exclude the preceding discovery request. They are not public-release-to-live
observation delays. One completed example per issuer cannot estimate a reliable
p95, filing-season throughput or market-incorporation window. Human review has
not occurred; its automatic validation check is not a measurement of review time.
LLM, real-time SIP and executable-order latency are **not measured**.

The Apple run preceded final envelope/cache/budget hardening. Its original records
are preserved, and the saved submissions were subsequently revalidated offline.
The Microsoft run registered the current audit code-file hashes and matches this
implementation. Neither measurement freezes the provisional 600-second deadline.

## Prior-disclosure findings

| Changed paragraph classification | Apple | Microsoft |
|---|---:|---:|
| Changed relative to prior comparable 10-Q | 42 | 103 |
| Exact wording in a captured earlier disclosure | 1 | 20 |
| Possible equivalent, requires review | 3 | 7 |
| Unresolved | 38 | 76 |

These are text-linkage counts, not distinct economic facts. Repeated wording may
refer to different periods, and absent matches may already exist in uncaptured
issuer releases. No paragraph was asserted to be new to the public. External
issuer-disclosure coverage and source-grounded human adjudication remain open.

## Engineering verification, separate from the probes

- **98 tests passed, zero skips**, in an isolated Python 3.12.14 environment with
  the unchanged requirements installed: 55 foundation tests and 36 new audit tests.
- Tests cover append-only integrity, as-of exclusion, tampering, SEC history and
  timestamp conflicts, prior/future disclosure separation, suspicious documents,
  fiscal comparisons, SIP pagination, nanosecond timestamps, quote/bar failures,
  missing statuses, denied stream access, capture caps and explicit abstention.
- A fully reviewed synthetic fixture exercises eligibility but cannot pass the
  real acquisition gate. No unit test result is counted as acquired market data.
- The unchanged 300-bar foundation demo completed. All 32 pre-existing files other
  than the approved ADR amendment matched their prior hashes before refreshing
  the checksum manifest. Existing runtime/broker/30-minute code is unchanged.

## Next gate

Use the implemented audit with a registered 25-issuer cohort and sourced SIP,
dated instrument/status, clock and earlier-disclosure inputs. Complete the
50-filing and manual extraction-quality checks in ADR 001 section 8. Continue or
abandon the candidate at that early gate; no need to wait years to reject it.

**Alpha research: not run. No LLM, forecast, optimizer, allocation, fill simulator,
order execution or multi-agent trading system was added.**

Preserved run IDs: `917522c8eff54883bc8c8db0fdd351a0` (initial Apple probe),
`e3bf29c836a54698a4f99928cc66fe44` (Microsoft probe). The companion
`10q_audit_evidence_20260915.zip` contains the original stores, reports and an
archive manifest with per-file hashes; raw evidence is excluded from Git.
