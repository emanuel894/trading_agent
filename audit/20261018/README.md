# Reproduce the long-term framework audit

Audit: [LONG_TERM_BUILD_VS_ADOPT_20261018.md](../../LONG_TERM_BUILD_VS_ADOPT_20261018.md).
Repository snapshot: `ad45afbf9aa1de402926b0a84da3e914faae5bd1`.
User date/timezone: 2026-10-18, Asia/Jerusalem. Actual retrieval/index clocks are
recorded separately in UTC; some native-Git file indexes supply only a UTC date.
No exact fetch timestamp is invented for those files.

This is source/document inspection. No third-party framework was installed,
imported, built, benchmarked or used for a model/data/broker call. GitHub/PyPI
and public documentation requests are metadata/source retrieval, not market-data
acquisition or provider-paid calls. Recommendations do not qualify production
coverage, broker execution, source truth, alpha or trading readiness.

## Source map

| File | Contents |
| --- | --- |
| `ai_sources.json` | TradingAgents T01–T19, RD-Agent R01–R20 and Qlib Q01–Q18 evidence IDs as present in the index; exact commits, full-file SHA-256/Git blobs, line ranges and quotations. T/R/Q references in the main audit resolve here. |
| `finrl_sources.json` | FinRL, official FinRL-X/FinRL-Trading, FinGPT, vectorbt and Backtrader: exact commits, full-file hashes and decisive ranges. |
| `execution_sources.json` | LEAN engine, IB/Alpaca plugins, Nautilus stable and development sources, docs/licenses and public HTTP metadata. |
| `execution_excerpts.md` | Twenty-seven decisive engine/broker/transition quotations at pinned paths and numbered source lines. |
| `quantrocket_sources.json` | Public client pin/source hashes and official mutable documentation/pricing captures; Apache client vs proprietary service distinction. |
| `core_sources.json` | SEC parser, FRED client, scikit-learn, MLflow, DVC, Prefect, LangGraph, analytical/calendar tools and alternatives; source HEAD/tag observations, immutable raw URLs and PyPI/docs hashes. |
| `critical_excerpts.json` | Additional byte-bounded FinRL-family/QuantRocket/FRED/Prefect quotations. Invalid UTF-8 in an upstream file is backslash-escaped, never silently replaced; the raw-byte offsets/hash remain authoritative. Some web quotations reference inert derived text, explicitly labeled. |
| `metadata_captures.json` | HTTP status, timestamp, path and response hash indexes for release/package/document retrievals. A Git tag, GitHub release and PyPI artifact are separate observations. |
| `raw_retention.json` | Cloud workspace raw-capture archive path/hash and file count. Raw third-party documents/code/data are not added wholesale to this repository. |
| `decisions.json`, `validation.json` | Final component decisions, unchanged-scope assertions and fresh repository/source verification. |

The packet verifies **604 distinct local indexed files**. This includes code,
documentation, metadata and four independent research notes; it is not a count
of 604 independent scientific sources or an assertion that every file was read
in full. Relevant implementations were read with surrounding context. Source
hash verification is integrity checking, not historical-validity or completeness
admission.

To reproduce source inspection elsewhere:

1. Read canonical `AI_PROJECT_POLICY.md` and the registrations from the reviewed
   repository snapshot. Audit documents do not override those rules.
2. Fetch the exact recorded commit, not moving HEAD. Obtain each recorded raw
   file or extract it from that Git object and check its full-file SHA-256/length
   against the manifest. Do not install/run upstream code to verify quotations.
3. Match the indexed line ranges/byte spans. Cross-check API defaults with the
   caller and downstream use; do not infer a safe workflow from a parameter name.
4. Treat current web pages/PyPI JSON as mutable. The retained hash identifies the
   captured version; a later fetch can differ. Persisted decisive quotations and
   recorded package versions/dates avoid silently replacing the audit's evidence.
5. Distinguish Git v0.9.8 Qlib from PyPI 0.9.7, Nautilus stable 1.x from 2.x HEAD,
   and open engine/client licenses from data/model/broker/service entitlements.

The raw archive remains in the cloud workspace at the indexed path, outside Git.
Pinned public source URLs can be fetched and hash-checked on another machine.
Mutable original web bodies may require the retained archive for exact full-page
reproduction; this limitation is explicit. No paid datasets, credentials or
private account responses are included.

Direct SEC/FRED/BLS/BEA/Federal Register, QuantConnect and QuantRocket documentation
was accessible during this audit. Some Fed/IB documentation routes were 403/404;
those failures are recorded and do not prove source incapacity. Older audit
network restrictions are not substituted for current observations.

Existing Python 3.13 repository tests/demo are regression checks only. No upstream
runtime, cross-engine parity, latency, licensed access or profitability result is
claimed. Hosted/Windows CI status is separate from local Linux verification.

## Issue #9 delta completion on the cleaned branch

The original packet above is preserved as historical evidence. Its reviewed
`ad45af...` identifier describes the original audit context, **not required Git
ancestry**. The maintainer's cleaned remote head
`4dd7703f429df01a6f7e67912294ec26e93b4ad0` is the parent for this additive
completion in existing PR #10. Do not merge or cherry-pick the old branch.

Read [delta_issue9/README.md](delta_issue9/README.md) for new Grok Bot / Claude
Code source captures, the live Issue #9 coverage map, four exact required outputs
and fresh validation. Earlier framework research is carried forward, not rerun.
The original `validation.json` remains unchanged and refers to the original
artifact hashes; it does not validate the updated report/README/decisions.
`delta_issue9/validation.json` records those replacements and preserved evidence.
