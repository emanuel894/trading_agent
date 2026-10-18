# Project state and authoritative source map

Version **1.1.0 — 2026-10-18**, Asia/Jerusalem. Snapshot, not standing authority for
later status claims. Refresh GitHub state on resume; update this map through review
when facts change, retaining dated evidence. Workflow rules newly consolidated in
the skill are operating instructions requested by the owner, not research amendments.

## Repository convention and discovery

Inspected `main` at `ebf676263343fc2049eb7e73cc5e83ab8c307c1f` and active
`feat/alpaca-paper-foundation` at `17f8742bf6fd64ca5733eb3b90b893d46172a753`
(after merged PR #10). The active branch has
root `AGENTS.md` → `AI_PROJECT_POLICY.md`; `CLAUDE.md` and `GEMINI.md` import the
same policy. No existing repo `SKILL.md` or nested agent instruction was found.
Keep one scientific policy and this one operating skill; no provider-specific copy.

`AGENTS.md` and the shared policy link [SKILL.md](../SKILL.md). Codex repo skill
discovery uses `.agents/skills/`; explicit invocation is `$trading-project`.
Other agents follow the policy link and read the same file as Markdown. This
matches [OpenAI's repo skill guidance](https://developers.openai.com/blog/skills-agents-sdk).
The package is available only on branches/checkouts containing it until human
integration; publishing this draft does not install it on `main` or in other chats.

## Science and current gates — read before research

- [Shared policy](../../../../AI_PROJECT_POLICY.md) and
  [ADR 001, especially §§5–8](../../../../trading_agent_starter/ARCHITECTURE_DECISION_001.md):
  first hypothesis is original 10-Q MD&A information beyond numbers and already
  observed market response. N/A/B/C comparisons, net costs, common opportunities,
  chronological fitting, trial limits, abstentions and untouched prospective
  confirmation are registered. Historical LLM results are exploratory. The old
  baseline → LLM → six-agent roadmap is superseded. Proposed capture dates passing
  does not establish capture or permit automatic date extensions.
- [003](../../../../trading_agent_starter/LIQUIDITY_AMENDMENT_003.md),
  [004](../../../../trading_agent_starter/ACQUISITION_SAMPLING_AMENDMENT_004.md),
  [005](../../../../trading_agent_starter/STRUCTURAL_IDENTITY_AMENDMENT_005.md):
  preserve provider-native Alpaca SIP raw daily liquidity, deterministic candidate
  priority/no replacement and the acquisition-only SEC-frame exception. Vendor
  independence cannot silently substitute a different liquidity definition.
- **FMBH rank #1 / CIK 0000700565 remains UNRESOLVED**; candidate #2, replacement
  cohort freeze, acquisition audit and alpha testing are not authorized by this
  package. Existing frozen artifacts must remain intact. Four Massive date-level
  responses do not establish exact-instant validity, continuous lineage or all
  potentially qualifying classes. Do not spend the remaining 58 calls for coverage.
  See [October 7 review](../../../../trading_agent_starter/FMBH_MASSIVE_SOURCE_REVIEW_20261007.md).
- Amendment 005 permits narrowly grounded retrospective **structural valid state**
  for acquisition feasibility despite unknown historical knowledge time. Keep
  effective, publication/revision and retrieval clocks separate; date-only stays
  date-only. It never backdates disclosures/features, quotes, halts or actionability,
  nor authorizes performance use. Missing/conflicting evidence stays unresolved.
- Progression remains source/eligibility qualification → valid registered freeze
  and acquisition/latency audit → separately authorized cheap controls/extraction
  and exploratory comparison → untouched confirmation/promotion → separately
  approved Paper/Live gates. Consult ADR §8 rather than copying thresholds here.
  Keep `TRADING_ENABLED=false`, `ALLOW_PAPER_ORDERS=false`, `ALPACA_LIVE_TRADE=false`.

## Architecture decisions and status

The merged [build-vs-adopt audit](../../../../BUILD_VS_ADOPT_20261017.md) retains
scientific admission/evaluation while preferring conditional LEAN integration and
Nautilus as challenger. [PR #10](https://github.com/emanuel894/trading_agent/pull/10) was squash-merged on
2026-10-18 as `17f8742bf6fd64ca5733eb3b90b893d46172a753`. Its final head
`13c691e0adbd9ed743f389c09515d134bcee2069` passed hosted Ubuntu and Windows CI.
The merged report and decisions include the Issue #9 Grok/Claude/multi-agent delta
and the exact TARGET_STACK, STOP_BUILDING_NOW, NEXT_3_TASKS and
API_AUTOMATION_VALUE_GATE outputs.

Target: qualified maintained historical master + official event evidence → immutable
objects/temporal issuer-class-listing bindings → frozen universes/features → cheap
numerical/text controls + removable LLM facts → independent registered evaluation
and deterministic risk → qualified engine → separately authorized Alpaca/IBKR adapters.
No broker assets, current ticker list or engine map becomes historical truth.

PR #10 recommends standard SQLite/object storage now; Parquet/DuckDB and DVC as
scale warrants; scikit-learn controls, EdgarTools parsing behind our evidence
validator, MLflow at the first authorized model stage, Prefect only for demonstrated
durable-job needs. LEAN is first to qualify, not installed/admitted. Its terminal
liquidation, plugin license and runtime boundaries need tests; engine license does
not prove free broker plugins. Nautilus is fallback, not a second production engine.
TradingAgents, RD-Agent(Q), Qlib, FinRL/FinRL-X are benchmark candidates, not a
replacement scientific authority. Preserve prototype risk/replay/ledger as
regression references; their defaults are not production certification.

Stop building generic security masters, backtesters/OMS, broker HTTP clients,
universal SEC parsers, ML libraries, schedulers, factor-agent loops and cross-provider
routers. Keep only demonstrated project-specific gaps; no core-fork platform build,
duplicate enterprise feeds or default multi-agent trade committee.

## Workstream ownership and stop boundaries

| Track | Verified state / next bounded result |
| --- | --- |
| Databento / [#7](https://github.com/emanuel894/trading_agent/issues/7), merged [#8](https://github.com/emanuel894/trading_agent/pull/8) | `DATABENTO_QUALIFICATION_NEXT`, not qualified. Read [RED review](../../../../trading_agent_starter/SECURITY_MASTER_RED_REVIEW_20261018.md), [decision](../../../../trading_agent_starter/research/structural_source_007_red/decision.json) and [provider request](../../../../trading_agent_starter/research/structural_source_007_red/PROVIDER_REQUEST.md). Repo records request **unsent**, no actual FMBH sample, unverified coverage start/price/free trial. #9/#11 describe waiting for a reply; reconcile owner evidence before asserting sent/replied or sending anything. Seek free static semantics/sample; stop before allocation/authenticated acquisition or purchase. |
| Stack / [#9](https://github.com/emanuel894/trading_agent/issues/9), merged PR #10 | Complete and merged as `17f8742bf6fd64ca5733eb3b90b893d46172a753`; exact-head CI was green. Reuse its report; do not repeat its framework/security-master audit. |
| LEAN / [#11](https://github.com/emanuel894/trading_agent/issues/11) | In progress on `research/issue-11-lean-contract-qualification`; two commits/checkpoint are pushed. Design and Q01–Q33 fixture matrix are drafted with provisional `LEAN_QUALIFICATION_READY`; independent review/final validation/draft PR remain. No LEAN fixture has been run. Resume from `trading_agent_starter/research/lean_qualification_011/PROGRESS.md`; do not restart source research. |
| Events / [#12](https://github.com/emanuel894/trading_agent/issues/12) | In progress on `research/issue-12-event-evidence-contract`; two commits/checkpoint are pushed. All requested design outputs are drafted with proposed `EVENT_SOURCE_QUALIFICATION_NEEDED`; independent review/final artifact hashes/draft PR remain. Resume from `docs/event-evidence/CHECKPOINT.md`; do not restart source capture. |

#11 and #12 can proceed independently of a Databento answer and use separate scopes;
both stop at design. Their current branches were created from the earlier foundation
head, so each must reconcile with the current foundation head before its final PR/CI
without restarting completed research. A third worker
is justified only for a distinct ready source-reply adjudication or integration
task, never merely waiting or duplicating #9. After #9, the default next-three
candidate list is source qualification, #11 and #12; rerank against live ownership,
dependencies and information value. No new work on these tracks is started by this skill.

## Automation, costs and CI

[Issue #5 activation](../../../../automation/real/ISSUE_5_ACTIVATION.md) remains
**PAUSED_BUDGET**, real acceptance not run; [control](../../../../automation/control.json)
is synthetic/provider-disabled. [Routing](../../../../automation/real/routing_policy.json)
has null actual model IDs/caps. Official Codex implementer and Gemini reviewer
runners plus a separate maintained publisher are intended, not activated. Max two
automatic repairs persist across resumes; global implementer/reviewer caps are 1/1.
Previously discussed illustrative API amounts and the RED review's proposed one-off
data ceiling are non-canonical and require fresh owner approval plus exact pricing/
enforcement; no fixed monthly API commitment is authorized and neither licenses paid calls. Broker/acquisition secrets
stay outside coding/review/ordinary CI. Human approval remains mandatory for merge,
science amendments, paid acquisition/activation, and later Paper/Live transitions.

Validation: [policy](../../../../AI_PROJECT_POLICY.md#validation-and-reporting),
[Foundation workflow](../../../../.github/workflows/tests.yml) and
[review/check design](../../../../CLOUD_AUTOMATION_PLAN_20261017.md#6-mandatory-checks-and-github-protection).
Run full unittest suite and demo from `trading_agent_starter` with Python 3.13;
confirm real Ubuntu and Windows job conclusions for the exact current head.
No specific Windows flaky-test root cause is established in this source map.
An email or one successful rerun cannot establish that a failure is harmless.

The owner's current Codex client exposes Goal mode and Plan mode. Use Plan for risky
path selection and Goal for long outcome-driven work. No heartbeat control has been
observed, so do not rely on heartbeat-based automatic resume; durable checkpoints
remain required when included usage is exhausted.
