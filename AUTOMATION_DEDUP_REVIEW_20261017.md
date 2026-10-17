# Issue #3 automation de-duplication review — 2026-10-17

**Decision: adopt maintained plumbing; retain project-specific acceptance guards.**
Reviewed implementation: `d7775efbd3bc97ce9cd43c66d0fc5cffd60e8b9e` on
`feat/issue-3-autonomous-dev-loop`, targeting `feat/alpaca-paper-foundation`.
This review revises that implementation without activating providers, publishing
synthetic PRs, changing science, or starting FMBH. Trading stays disabled.

OpenHands already implements substantial issue → branch → PR → review-feedback
plumbing. We should not build a competing scheduler, conversation runtime or PR
framework. Its current issue-to-PR integration is **not a safe drop-in under our
policy**: the coding agent holds a GitHub write token and publishes its own work.
The immediate safe reduction replaces custom API/download transport with official
GitHub actions and removes fake branch/PR descriptors. The remaining controller
is an offline acceptance harness, not our proposed production orchestrator.

## Evidence and scope

Inspected actual code, action schemas, examples, licenses and Git refs at the
following revisions, retrieved on this date. These are source snapshots, not a
claim that every HEAD is a qualified production release. License observations
apply to repository code; hosted services/models have separate terms and costs.

| Upstream | Inspected commit | License / relevant maintenance evidence |
| --- | --- | --- |
| OpenHands/OpenHands | `61a3bd93e642a0ff4def73b29496a73245628209` | MIT; current README separates Agent Canvas, SDK and automation. Old resolver paths are not the current integration. |
| OpenHands/automation | `bc4cca7c7e2eab5cb7d0ff671bec5dd113d3e2c2` | MIT; package 1.20.1, Python >=3.12, explicitly beta; dispatcher, run models, presets and service CI exist. |
| OpenHands/extensions | `d05780951082d4d83f785cb1d4c7f2be6d1c14a5` | MIT; maintained issue-to-PR scripts/catalog, PR-review plugin and dedicated tests. This is where the relevant automation lives. |
| OpenHands/software-agent-sdk | `5966c781ed014efc96c028a99bddd4ff78426741` | MIT; conversation/tool/workspace runtime, persistence tests and GitHub workflow examples. |
| obra/superpowers | `bb92a77741419a4ab5f06e711a283343f1ada0c3` | MIT; concrete planning/TDD/implementation/review/finishing skills. |
| google-github-actions/run-gemini-cli | `387c8ddb7a72078825da941758b811b9153c71e8` | Apache-2.0; official action schema, authentication docs and dispatch/review examples. |
| openai/codex-action | `a8d8be6ee028bea4525bc722d16f36687b408c81` | Apache-2.0; official CLI/action source, permission profiles, proxy and security guidance. |
| actions/github-script | `ed597411d8f924073f98dfc5c65a23a2325f34cd` | MIT; v8.0.0, Node 24; Octokit/runtime source inspected. |
| actions/download-artifact | `37930b1c2abaa49bbe596cd826c3c89aef350131` | MIT; v7, Node 24; cross-run artifact inputs and download source inspected. |

[Source inventory](automation/dedup_sources_20261017.json) records immutable URLs,
byte counts and SHA-256 hashes. Successful retrievals are distinguished from
failed guessed paths. No upstream agent code was installed or executed, no
provider was called, and source inspection is not a security certification.
Official GitHub actions' READMEs say external contributions are currently closed;
they remain GitHub-maintained runtime integrations, not a promise of support or
future API stability. No popularity measure determined a recommendation.

## Upstream overlap and adoption boundaries

### OpenHands: substantial lifecycle overlap

The current [issue worker][oh-worker] selects labeled/dependency-ready issues,
maps existing branches/PRs, dispatches implementation and revises an existing PR
after `software-factory/review` failure/error. Importantly, it reads that status
at the PR's **exact head SHA** and puts that head in the revision request. The
[conversation dispatcher][oh-conversations] uses subject/delivery identifiers
for idempotent delivery and can read model/profile provenance back from the
conversation. These are real lifecycle capabilities; describing
OpenHands as just an LLM demo would be incorrect.

The [main script][oh-main] also has persistent claimed/starting/active/finalizing
states, launch limits and recovery/finalization behavior; the
[state schema][oh-state] documents them. [Automation service code][oh-service]
supplies scheduling/dispatch and run storage; the [SDK examples][oh-sdk] supply
agent execution and persistence. These layers solve different problems. Running
the service adds PostgreSQL/service/sandbox operations and beta-version coupling;
it is more infrastructure than this synthetic milestone requires.

The [README][oh-readme] explicitly gives the coding conversation
`GITHUB_PERSONAL_ACCESS_TOKEN` with contents/PR/issues write and recommends
workflow scope. The agent commits, pushes and opens the PR; Python fallback
publication verifies/retries that outcome. Secret allowlisting and exclusion of
deployment MCP servers are useful controls. Setting the agent secret allowlist
to `[]` removes that token but does not by itself establish a supported
patch-only worker plus separate exact-base publisher. Current worker prompts
instruct cloning/branching and publishing; the legacy preparation path clones
the moving default branch. A base SHA in a prompt is not enforced checkout or
trusted-policy loading.

Neither its per-poll launch cap, delivery key, finalization retries nor exact-head
review status proves our **two repairs across resumes**, registered scope,
pre-call spend reservation, or fail-closed admission. Its existing state should
be used for generic run lifecycle; our small policy receipt/counters would bind
that lifecycle to the project contract rather than duplicate its event log.
The shared dispatcher already caps conversation-error retries at two, but resets
that counter for a new delivery. That is not a two-repair limit across PR heads.

**Disposition: INTEGRATE conditionally for production lifecycle; do not deploy
unchanged and do not fork/rebuild it here.** Substantial replacement is credible,
but safe replacement is not demonstrated at this revision. A later qualification
must show a supported no-write-token coding worker, bounded patch output, fresh
publisher runner and exact-base/head admission, with durable caps/budget binding.
If those boundaries cannot be configured, keep supervised publication while
evaluating upstream support; that is not permission to start a custom platform.

The SDK's basic GitHub example grants writes in the model job, installs packages
from moving `main` and downloads a remote script. The PR-review plugin also has
publication privileges. Do not copy those examples as our security boundary.

### Superpowers: integrate the development process

[Subagent-driven development][sp-dev] already provides implementer/spec/code
review roles, fix findings, scoped re-review and a persistent findings ledger.
[Finishing][sp-finish] covers branch integration/PR preparation. Reuse this
process rather than inventing repository prompt chains or a second development
methodology. It is instruction content, not a hosted scheduler, GitHub token
boundary, spend meter or deterministic policy engine.

At this revision the default fix loop allows **five** rounds, including model
escalation in later rounds. Our hard maximum remains **two**, without an extra
final-review repair allowance. Project policy also overrides worktree defaults
and any merge option: existing isolated checkout, human merge, no automatic
publication privilege. Model identity and a fresh context still need verification;
two conversational roles alone are not independent model review.

**Disposition: INTEGRATE process; KEEP_OURS enforceable project controls.**
No new orchestrator package or automatic subagent fan-out was added in this review.

### Gemini: adopt the official runner, not its review permissions wholesale

The [action schema][gemini-action] handles CLI setup, auth/settings/prompt inputs
and outputs. Its authentication docs cover API keys and Google workload identity.
The actual [review example][gemini-review] mints a PR/issues-write token, sets
`GEMINI_CLI_TRUST_WORKSPACE=true`, permits review-writing MCP tools and sets
25 session turns. The dispatch example is useful event plumbing, not our
maintainer authorization or two-repair contract.

**Disposition: INTEGRATE the official action for the future Gemini challenger;
DROP plans for a custom Gemini HTTP/CLI client.** Qualify a read-only static
review bundle, trusted settings, bounded tools/turns and separate comment
publication. Do not copy public event triggers, workspace trust, extension
loading or token permissions unexamined. Authentication support alone does not
prove raw-key isolation, billing limits or scientific boundaries.

### Codex: adopt the official execution boundary

The [action schema][codex-action] and [security document][codex-security] provide
CLI installation/execution, Responses proxy, permission profiles, actor controls,
structured output and privilege strategies. The README demonstrates separate
read-only model and write-capable comment jobs. This aligns better with our
separate publisher than putting GitHub write credentials inside the coding agent.

`:workspace` has network disabled by default; process privilege reduction is a
separate control. Use trusted `codex-home`/configuration, pinned CLI/model/action
versions and a qualified Linux runner; candidate-controlled settings must not
define privileges. A proxy protects credential handling but does not create our
task budget ledger or source-policy authority. The action does not itself supply
a complete issue-to-PR service.

**Disposition: INTEGRATE official Codex action for future implementation;
DROP plans for a custom OpenAI client/conversation runtime.** Keep OpenAI as
implementer and Gemini as the first independent reviewer target, as Issue #3
specifies. Do not add Claude or an additional OpenHands model role for novelty.
OpenHands would replace lifecycle infrastructure, not become a third voter.

## Every current custom component

Classification distinguishes actual offline acceptance code from functionality
that has never been implemented for real GitHub/model operation.

| Current component | Classification | Result / reason |
| --- | --- | --- |
| `control.py` exact Git-object policy/config loading | KEEP_OURS | Trusted-base authority and strict disabled configuration are project predicates. Upstream prompt discovery cannot replace them. |
| `safe_path`, typed result validation, science/control-path exclusion | KEEP_OURS | Scope/scientific contract and fail-closed admission; candidate content cannot authorize itself. No scientific files become admissible. |
| Exact synthetic head matching for CI/review | KEEP_OURS | Acceptance contract tested offline; production must compare real current base/head immediately before writes/readiness. OpenHands exact-head status handling is useful but not sufficient. |
| Two-repair/six-call caps, zero-cost pre-call pause, terminal failure handling | KEEP_OURS | Cross-resume project limits, including outages/unknown evidence. Current harness is zero-cost only; a real monthly spend ledger is still unimplemented. |
| Hash-linked task snapshots, context binding and local owner lock | KEEP_OURS | Auditable policy/counters/resume acceptance. Not a general event store, malicious-rewrite proof or production distributed lock. |
| `Controller.run`, `_call`, implementer/reviewer/CI protocols | KEEP_OURS, offline scope only | Drive negative guard tests without models or candidate execution. Do not extend them into production conversations, scheduling, GitHub clients or publication. Delegate lifecycle to maintained tools when qualified. |
| `fixtures.py` deterministic worker/CI/reviewer | KEEP_OURS | Zero-key safety acceptance, not a replacement for Codex/Gemini or real independent review. |
| `__main__.py`, `__init__.py` CLI/tool version | KEEP_OURS | Local reproducibility/resume identity only; version 2 rejects old-shape journals. |
| Fake branch/PR descriptor | DROP | Removed. It provided no GitHub capability or necessary guard evidence; synthetic content head remains for stale-result tests. |
| Manual workflow trigger, concurrency, timeout, CI and artifact publication | INTEGRATE | Existing GitHub Actions own scheduling, serialization, storage and tests. Preserve original Foundation CI unchanged. |
| Inline `gh api` subprocess transport | REPLACE | Now pinned `actions/github-script` / Octokit; retain only our repository/actor/SHA/issue/resume predicates. |
| Inline `gh run download` transport | REPLACE | Now pinned `actions/download-artifact`; verified source-run identity selects the exact artifact name. Missing/untrusted artifacts fail closed. |
| Handwritten Actions-summary formatter | REPLACE | Now `core.summary` via github-script; current controller failure cannot reuse restored historical READY status. |
| Local restored-task-ID binding | KEEP_OURS | Small project identity check; full journal/policy/version/counters still verified by the harness. |
| `automation/control.json` | KEEP_OURS | Explicit project targets/limits and disabled providers; no generic provider routing configuration. |
| Bootstrap tests and recorded validation | KEEP_OURS | Regression evidence for our controls, including execution of the actual JS guard with synthetic Octokit replies. |
| Runbook/cloud plan | INTEGRATE | Specify maintained upstream process/runners/lifecycle and the project overlay; no parallel instruction copies. Canonical policy/provider entry files unchanged. |
| Historical validation metadata | KEEP_OURS | Preserve the original result; append this review's validation and source inventory separately. |
| Future custom issue polling, branch/PR/review publisher framework, provider clients | DROP | Not implemented now; remove them from the development direction. Qualify maintained lifecycle/runners first. A minimal project validation gate is still required at any eventual write boundary. |

## Applied changes and remaining qualification

The manual synthetic workflow remains read-only, fixed to the trusted base ref
and exact SHA, with no secrets bindings or model SDK dependency. Both replacement
actions are full-SHA pinned; they use Node 24 and require runner >=2.327.1.
GitHub-hosted Ubuntu is the target; no self-hosted runner/GHES support is claimed.
Only trusted action code receives the ephemeral read token. Fixture roles receive
allowlisted data, never process environment or issue prose. They are **not an OS
sandbox for arbitrary agent plug-ins**.

The pinned downloader's `src/download-artifact.ts` warns and continues on
`digestMismatch`; it is not a cryptographically fail-closed archive gate. Current
read-only synthetic acceptance still requires the exact trusted source run and
valid journal/context/hash chain, which reject malformed/stale state but cannot
prove against a fully rewritten/rehashed journal. Before privileged publication,
qualify a supported hard integrity check binding the actual artifact/patch bytes
to a trusted receipt. Do not infer that property from download success. This
review does not activate a publisher or weaken its qualification requirements.

Production integration is deliberately inactive. The next automation work, if
authorized, should qualify upstream boundaries with synthetic transport, not
write a new scheduler or enable billing. Demonstrate all of:

1. Policy/config from the registered trusted base even if candidate instructions
   are hostile; current base/head changes invalidate work.
2. Implementer/reviewer have no GitHub write, broker, acquisition or deployment
   credentials; reviewer has a fresh context and distinct model identity.
3. Separate publisher accepts bounded validated output only, with no candidate
   execution and no protected-branch/merge authority.
4. A real task/PR identity keeps repair counts and spend reservations across
   deliveries/retries; exhaustion and ambiguous calls pause/block before further
   paid work. No automatic fresh-task escape from caps.
5. Mandatory CI and review refer to the exact final head; missing, stale or
   unavailable evidence blocks readiness. Human approval/merge stays required.

Small action substitutions have low migration cost and no model usage cost;
GitHub runner/artifact charges can still apply. OpenHands service adoption has
material operations/integration cost and beta compatibility risk. Do not deploy
that stack just to replace a synthetic fixture. Official actions avoid bespoke
client maintenance but still couple to provider auth/CLI behavior; keep the
bounded patch/review receipt portable. No unsupported estimate of provider
quality, security or review savings is asserted.

## Verification

Fresh results are recorded in
[dedup validation](automation/dedup_validation_20261017.json). The new guard tests
first failed on the old transport, then passed with maintained-action integration.
The full existing suite, synthetic demo, registration verification, workflow lint
and protected-file diff are checked separately. Windows/hosted CI and real
provider isolation are not established by local Linux tests. No provider, data,
broker or order call was made. FMBH remains UNRESOLVED.
An independent fresh-context code reviewer found no blocking changes, reran the
36 guard tests and checked all 72 inventoried source files. A helper-source
symlink citation was corrected to the actual shared implementation; the download
digest limitation above was recorded. This review is not the future independent
Gemini provider check, which remains inactive.

Stop state: **AUTOMATION_DEDUP_READY** (review and inactive synthetic revision).

[oh-worker]: https://github.com/OpenHands/extensions/blob/d05780951082d4d83f785cb1d4c7f2be6d1c14a5/skills/github-issue-to-pr/scripts/worker.py
[oh-conversations]: https://github.com/OpenHands/extensions/blob/d05780951082d4d83f785cb1d4c7f2be6d1c14a5/skills/github/scripts/agent_conversation.py
[oh-main]: https://github.com/OpenHands/extensions/blob/d05780951082d4d83f785cb1d4c7f2be6d1c14a5/skills/github-issue-to-pr/scripts/main.py
[oh-state]: https://github.com/OpenHands/extensions/blob/d05780951082d4d83f785cb1d4c7f2be6d1c14a5/skills/github-issue-to-pr/references/state-schema.md
[oh-readme]: https://github.com/OpenHands/extensions/blob/d05780951082d4d83f785cb1d4c7f2be6d1c14a5/skills/github-issue-to-pr/README.md
[oh-service]: https://github.com/OpenHands/automation/blob/bc4cca7c7e2eab5cb7d0ff671bec5dd113d3e2c2/openhands/automation/dispatcher.py
[oh-sdk]: https://github.com/OpenHands/software-agent-sdk/tree/5966c781ed014efc96c028a99bddd4ff78426741/examples/03_github_workflows
[sp-dev]: https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/subagent-driven-development/SKILL.md
[sp-finish]: https://github.com/obra/superpowers/blob/bb92a77741419a4ab5f06e711a283343f1ada0c3/skills/finishing-a-development-branch/SKILL.md
[gemini-action]: https://github.com/google-github-actions/run-gemini-cli/blob/387c8ddb7a72078825da941758b811b9153c71e8/action.yml
[gemini-review]: https://github.com/google-github-actions/run-gemini-cli/blob/387c8ddb7a72078825da941758b811b9153c71e8/examples/workflows/pr-review/gemini-review.yml
[codex-action]: https://github.com/openai/codex-action/blob/a8d8be6ee028bea4525bc722d16f36687b408c81/action.yml
[codex-security]: https://github.com/openai/codex-action/blob/a8d8be6ee028bea4525bc722d16f36687b408c81/docs/security.md
