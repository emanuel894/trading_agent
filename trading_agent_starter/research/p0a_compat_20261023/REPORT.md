# Bounded authentic-format repair — 2026-10-23

**PASS: the two demonstrated format defects are repaired with narrow permissions.**
**FAIL: authentic preparation remains blocked; decision `P0A_INCOMPLETE`.**
One accession (`0000950170-25-067613`), two representations, one attempt each.
Coverage is **1/12 authentic filings**, with **0/1 successful authentic MD&A
extractions**. Neither source clocks nor representation conflicts are qualified.

## Change and security evidence

Base PR46 `fe7cb972794ad1ec50a88467c08eab71841fb428`; processing commit
`cfe4a1b99e7f7555b003d1126b1caf277a5656aa`, module SHA256
`22600e3afbc3ebae4df5bd68e9917230b118c26385f3dfe9a05fa532b95a1f85`.
PR45 remains at `46737267dac2f15ab45bb032490cefebc79b39ea`.

- `agent/p0a_mda.py`: admits only the observed `meta` pair
  `http-equiv="Content-Type" content="text/html"` directly inside `html/head`.
  No generic `http-equiv`/`content` permission. Recognizes one attribute-free
  whole-TEXT XBRL envelope only after submission identity/primary selection;
  original byte offsets advance by the exact prefix length. Inner markup still
  passes the unchanged strict HTML/CSS checks. Algorithm lineage advances to v3.
- `tests/test_p0a_mda.py`: five new methods reproduce both original failures,
  validate entity/Unicode original-byte maps and exhibit isolation, and reject
  refresh/cookies, wrong metadata values/context, duplicates, missing values,
  event handlers, malformed/nested/multiple wrappers, outside text, primary-role
  wrappers, scripts, iframes and unsupported visibility/CSS.
- This packet adds measurements, structural byte diagnostics, the reused local
  replay driver and validation receipts. No shared collector, source evidence,
  inference adapter, protected registration, trading or policy changes.

The positive tests failed at the two demonstrated codes before implementation.
After repair: **38 focused tests and 382 full tests passed, zero skips; demo
exited 0**, existing Python 3.12.14 dependency environment. Negative cases and
existing hidden iXBRL/nested table/provenance regressions pass. Independent review
and exact-head Ubuntu/Windows CI receipts belong in the new draft PR conversation.
No human or qualified cross-provider acceptance is claimed.

## Original-byte replay

Read-only input: `runs/p0a-g4-import/g4-20261021`, receipt
`DESTINATION_VERIFIED_READ_ONLY`. Manifest/verifier hashes and all 15 extracted
files were verified before and after processing; every imported mode remained
nonwritable. SQLite opened `mode=ro&immutable=1`, query-only, trusted-schema off.
All 29 original records verify; chain head remains
`dce9e60f780b902cb7f157d5abee8c184998cacbcba31aa11714ddfbd3b79806`.
Each complete original response, failure and timing receipt is preserved in a
separate seven-record output chain; details/hashes are in `measurement.json`.

Direct primary SHA256 begins `7813247a` (7,306,025 bytes); submission begins
`306a47c1` (30,606,368 bytes). Full hashes are in the machine-readable packet.
Both now reach the original body tag and fail **`UNSUPPORTED_CSS`** on
`padding:8px;margin:auto!important;z-index:0;position:relative;`.
The direct primary also contains a script element at original byte interval
`[7305894,7306009)`; inert inspection found no script in the selected submission
primary. The script is not reached by this replay because CSS fails first;
dedicated negative fixtures prove script rejection after the repaired formats.
Nothing was removed or sanitized to manufacture a successful preparation.

| Measurement | Direct primary | Complete submission |
| --- | ---: | ---: |
| Source read seconds (outside process timer) | 0.008120 | 0.046458 |
| Identity/provenance seconds | 0.087472 | 0.174187 |
| Parsing to CSS failure seconds | 8.555721 | 8.557362 |
| Persistence seconds | 0.028003 | 0.101782 |
| Other process overhead seconds | 0.002861 | 0.002141 |
| Total processing to failure seconds | 8.674057 | 8.835472 |
| CPU seconds | 8.654833 | 8.819687 |
| Traced Python peak bytes | 45,700,796 | 76,301,932 |
| Process high-water RSS bytes | 69,853,184 | 120,709,120 |

Single instrumented attempts, not a benchmark distribution. RSS is cumulative
Linux process high-water; Python allocation peaks include source read and tracing
overhead. Parser construction builds byte offsets before reaching the failed tag.
Persistence excludes the final timing receipt's own write. These durations are
neither successful MD&A processing nor G4's 24.608-second acquisition session.

## Unmeasured evidence and stop state

MD&A extraction, normalization, chunking and validation: **NOT_RUN**, null latency.
No authentic text, chunks, assertions or extracted MD&A source spans were produced.
Real inference, tokens, quality, inference memory/cost and end-to-end LLM latency:
**NOT_MEASURED**, no mock inference. No configured authorized zero-spend research
route exists; current environment readiness exposes no credentials/capabilities.

The next blocker is an explicitly bounded HTML/CSS visibility decision, including
the primary's script, before any new extraction experiment. This repair stops at
the authorized two format defects. Reuse the existing parser/evidence store and
failure packet; no broader sanitization, parser rewrite or repeated source search.
Then, only if preparation succeeds, a qualified zero-spend inference route can
enable the separately measured real-inference experiment. Twelve-source coverage
and independent assertion-support evidence would still be required for original
acceptance. One implementer and one fresh reviewer; serving model IDs/effort are
unavailable, requested reviewer preset is recorded in its receipt.

Critical path remains source-safe preparation, then authorized inference; both
are blocked. The new draft is reviewable and remains unmerged. No new SEC, model,
market or broker requests; no stock returns, labels or alpha inspected. G4 physical
clock uncertainty, acceptance-time conflict and representation-size differences
remain **unresolved**. External spend **$0**.

Replay output location: `runs/p0a-g4-output/replay-20261023-compat-01`.
`replay_originals.py` is an exact retained copy of that one-off orchestration,
using this session's already-verified source/attachment paths; it is not a new
general runner. Run only from a fresh sibling output directory with the same
layout and import paths, never against an existing output store or imported root.
The earlier failure packet and G4 acquisition/review are retained unchanged.
