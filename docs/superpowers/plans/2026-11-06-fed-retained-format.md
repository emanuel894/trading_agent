# Retained Fed statement adapter implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline; obtain one fresh independent review of the final branch.

**Goal:** Extract supported deterministic facts from the already retained M02 HTML without acquiring data or admitting predictive information.

**Architecture:** A small standalone offline adapter verifies the existing archive and manifest against trusted-base pins, then extracts facts with original UTF-8 byte spans. It leaves the synthetic chart demonstration unchanged. A frozen loaded document supports catalog cutoff views; it cannot reconstruct historical receipt or source revisions.

**Tech stack:** Python standard library, Decimal, regular expressions, gzip and unittest. No dependencies added.

**Spec:** Owner's “Resume the Trading Agent Build, Evidence-Driven Implementation” request, Workstream A, received 2026-11-06; canonical policy and docs/event-evidence/CONTRACT.md at base 5f8b850548e2f7786814086d5350a72a19d87459.

## Global constraints

- Dedicated branch: feat/fed-retained-format-adapter-20261106; no merge.
- Original SEC, IQ-P1 and prospective event protocols and holdouts remain unchanged.
- No source acquisition, inference, strategy returns or broker actions.
- Preserve M02 bytes, archive/manifest hashes and actual 2026 retrieval time; unknown historical clocks remain unknown.
- The 2024 first edition is unproved. All output remains catalog-only and predictively quarantined.
- Independently admissible prior statement/setting is unavailable in the retained packet. Stop rate-change and statement-diff computation at that dependency; return null with an explicit abstention. Do not substitute the current statement's own asserted cut or synthetic context.
- Unsupported revisions fail closed; do not build a collector, version store or generic admission framework.

## Review focus

1. Inflation objectives and dissenting preferences must not become the target rate.
2. Fractional percentages, conflicting ranges and unsupported units fail safely.
3. Spans resolve to original raw bytes, including after non-ASCII text.
4. Date-only/minute source labels and unknown receipt cannot create historical availability.
5. Changed archives/manifests and later files cannot rewrite a previously loaded document or its earlier catalog view.

## Task 1: Bound authentic format extraction

**Files:** Create agent/fed_statement_offline.py and tests/test_fed_statement_offline.py under trading_agent_starter; add a short result/checkpoint under docs/event-evidence/. Pin captures.json checkout bytes with one .gitattributes entry for Windows parity.

**Interfaces:** load_retained(source_directory=None) returns a frozen RetainedStatement. RetainedStatement.snapshot(cutoff) returns a new catalog-only dictionary. A private text parser returns target-range and fixed-marker facts or raises ValueError; it does not admit sources.

- [x] Write tests against the real retained archive: literal expected target bounds 4.75 and 5 percent; markers; raw-byte span round trips; missing prior context; unknown clocks; strict retrieval cutoff.
- [x] Write rejection tests for archive/manifest tampering and missing files; explicitly synthetic malformed-format tests for conflicting ranges, units, fractions and unsupported markup; frozen-view tests after attempted late replacement.
- [x] Run tests and retain the expected initial failure before implementation.
- [x] Implement only pinned-source loading, template-specific deterministic parsing and catalog snapshots. No comparison engine while the independent comparator is absent.
- [x] Run focused tests, required full suite and repository demo in an isolated dependency environment. Do not inspect the demo performance artifact.
- [ ] Record source limits, commands/results, exact base/head and next dependency. Verify protected artifacts unchanged.
- [ ] Obtain independent review; repair substantiated findings with tests; publish one draft PR and run existing Ubuntu/Windows CI. Keep unmerged.

Ruling: the owner's absent-context abstention requirement permits standalone current-document facts; the unavailable comparator stops only dependent rate-change/diff outputs. This is not a completed historical comparison capability.
