# Issue #3 — synthetic autonomous development control

Issue #5's real-provider activation is tracked separately in the
[activation qualification](real/ISSUE_5_ACTIVATION.md). It is currently
`PAUSED_BUDGET`; the draft routing policy does not enable provider execution.
This existing synthetic harness and its limits remain unchanged.

This implements the **dry-run milestone** of
[Issue #3](https://github.com/emanuel894/trading_agent/issues/3), under
[AI_PROJECT_POLICY.md](../AI_PROJECT_POLICY.md). The owner explicitly selects
OpenAI/Codex as the future implementation target and Gemini as the first reviewer
challenger; provider interfaces are replaceable. Claude is deferred. That newer
direction supersedes the original plan's provider recommendation and sequencing,
without amending science or starting FMBH.

## Exactly what works

`devloop` is a standard-library-only **project guard acceptance harness** with fixture implementer,
fixture CI and fixture reviewer boundaries. The two role instances exchange typed,
bounded data without a human relay. No CLI key is needed, no external provider is
called, no candidate code is executed, and no candidate change is applied to the
checkout. A synthetic content head exercises stale-result rejection;
**it is not a real GitHub commit or an independent model review**. The former
synthetic branch/PR descriptor was removed in the
[de-duplication review](../AUTOMATION_DEDUP_REVIEW_20261017.md).
Creating real feature PRs and unattended API-backed work needs later activation.

Do not evolve this harness into a custom issue scheduler, provider client,
branch/PR publisher or agent conversation manager. Adopt maintained plumbing
where its permission boundary qualifies; retain our project-specific guards.
The source-pinned review documents the OpenHands lifecycle candidate,
Superpowers development process and official Codex/Gemini runner choices.

The existing Foundation PR test workflow remains unchanged. The new manual
workflow separately runs the complete suite/demo before its synthetic controller.
The controller's `tests: 2` record represents two actual deterministic fixture
checks (allowed change path and expected synthetic content format), not the
Foundation suite. Its reviewer finds a deliberately planted fixture marker.
These checks establish control behavior, not model quality or scientific alpha.

```text
QUEUED -> IMPLEMENTING -> TESTING -> REVIEWING -> READY_FOR_HUMAN
                             |          |
                             +---- REPAIRING -> IMPLEMENTING

invalid/stale/failed inputs -> BLOCKED
insufficient per-run budget -> PAUSED_BUDGET (before provider call)
```

At most two repairs, six total fixture-provider attempts, and one controller
owner per task are allowed. A request for a third repair becomes `BLOCKED` with
`REPAIR_CAP_REACHED`. There is no auto-merge operation or merge/admin credential.
Terminal runs are immutable on resume: `READY_FOR_HUMAN`, `BLOCKED` and
`PAUSED_BUDGET` cannot be reset by restarting the controller. A paused budget is
an owner-triage condition, not automatic permission to raise caps. Real budgets
and a cross-run monthly spend ledger are not activated in this zero-cost mode.

## Local acceptance on a committed control revision

Use an isolated Python 3.13 environment with the existing `requirements.txt`
installed. From `trading_agent_starter`, use the **full SHA of the local committed
revision containing the controller/config** (not a symbolic ref):

```bash
python -m unittest discover -s tests -v
python -m devloop --base-sha FULL_40_CHARACTER_COMMIT_SHA --issue-number 3 --scenario happy --output /tmp/devloop-happy
python -m devloop --base-sha FULL_40_CHARACTER_COMMIT_SHA --issue-number 3 --scenario repair-once --output /tmp/devloop-repair
```

Expected: `READY_FOR_HUMAN`, exit 0, summary stop state
`AUTOMATION_DRY_RUN_READY`. Generated `state.json` records exact source base/head,
source-policy hashes, code/tool version, synthetic candidate head, role/model
identities, tests, reviewed head/findings, repairs/retries, active provider/CI
elapsed milliseconds, timestamps, and estimated/model-reported cost. Estimated
and fixture-reported costs are zero; real unknown costs would remain null rather
than invented. `summary.json` explicitly says no real PR/model review occurred.

Run/resume the **same** directory with `--max-steps 3` initially and omit that limit
next time. It stops at `REVIEWING` without claiming readiness, then resumes from
the journal with the original counters. The partial invocation exits 2 because
it is incomplete. Do not edit a saved record to make it pass. The exact issue,
base, policy/config, scenario and task identity must match on resume. A local
fixture issue hash is generated unless a verified GitHub snapshot hash is given.
Tool version `synthetic-devloop-2` deliberately rejects journals from version 1;
their task shape and policy binding differ. Use a fresh synthetic task on the new
committed control revision. This is not permission to reset a real PR's counters.

Negative scenarios, each using a distinct output directory:

| Scenario | Required result |
| --- | --- |
| `repair-cap` | `BLOCKED`, exactly 2 repairs / 6 attempts, no third repair |
| `provider-failure` | `BLOCKED/PROVIDER_FAILED`, sanitized error only |
| `budget` | `PAUSED_BUDGET`, zero provider attempts |
| `stale-review`, `stale-ci` | `BLOCKED`, results from a different head rejected |
| `path-escape`, `control-path` | `BLOCKED`, no proposed change admitted |
| `ci-failure` | failed fixture content never becomes ready; two repairs then block |

All negative/incomplete runs exit 2; they must not turn a hosted workflow green.
Tests additionally exercise ambiguous JSON, corrupt journals, changed policy/base,
symlink paths, concurrent owners, zero-test/pending/non-secretless CI, inactive real
providers and untrusted nested instructions. Fixture sources are explicit in
`devloop/fixtures.py`; no mock result is labeled a real provider result.

## Maintainer workflow — GitHub is the persistent task source

After human review/merge, make the workflow discoverable on the repository's
default branch through the normal reviewed process; GitHub requires that for
`workflow_dispatch`. Do not push directly to a protected branch or weaken its
rules to expose the button. Dispatch the workflow with **ref
`feat/alpaca-paper-foundation`**, once that branch contains the accepted control
revision. It deliberately refuses execution from a PR feature ref or an old SHA.
Before that, local/temp-repository acceptance works but no hosted run is claimed.

In Actions → **Autonomous development dry run** → Run workflow:

1. Choose `feat/alpaca-paper-foundation` as the workflow ref.
2. Supply an open, maintainer-authorized issue number and the branch's exact
   current 40-character SHA. Choose `happy` or `repair-once`; `max_steps=50`.
3. Read the run summary and download
   `autonomous-dev-issue-N-RUN_ID-ATTEMPT`. The artifact contains the entire
   hash-linked journal and summary. It records the issue snapshot hash; issue
   bodies are not placed in fixture prompts, logs or published artifacts.
4. To demonstrate resume, first use `max_steps=3`. In a subsequent dispatch supply
   that completed run's ID as `resume_run_id`, with the same issue, scenario and
   exact base. The workflow verifies repository, workflow path, ref, event, source
   SHA and completion before downloading its exact artifact. The controller then
   verifies context, counters, content heads and the hash chain. It preserves the
   original task ID. A changed issue snapshot or unavailable artifact blocks.

GitHub holds task input, run history, status and immutable-per-run artifacts;
chat history is not needed. A successful resume produces a new artifact with the
previous event prefix intact. Retention is 30 days: download/archive under an
approved retention policy before expiry, or stop if the trusted artifact is gone.
Hashes detect accidental/casual alteration, not a malicious party rewriting and
rehashing a complete journal; trust also depends on the verified GitHub source
run and branch controls. No external timestamp/WORM claim is made.
The maintained downloader warns rather than fails on archive digest mismatch.
Download success alone is not integrity evidence; the source-run/journal guards
remain required. A future privileged publisher additionally needs a qualified
hard integrity check against a trusted receipt of the patch/artifact bytes.

Concurrency groups serialize all runs for an issue, across source SHAs; the
controller lock also prevents concurrent local owners of the same journal. This
is stricter than separate per-role concurrency for the one synthetic PR per task.
Fresh dispatches create distinct synthetic tasks, not additional repair rounds on
a real PR. Do not transplant this into a live PR loop without durable, authoritative
PR identity/counters and stale-review handling across every worker/publisher.

## Trust and credential boundary

The inline workflow bootstrap validates exact branch/runtime/workflow/current
remote SHA, actor write/maintain/admin permission, an open non-PR issue and bounded
input formats before repository code runs. Checkout uses an audited full Action
SHA, exact base and `persist-credentials: false`. Python/config/policies come from
that base. `load_trust` reads policy/config Git objects, verifies source HEAD and
matching local control bytes; it does not discover nested instructions or load
candidate hooks, plugins or MCP configuration.

Pinned `actions/github-script` supplies Octokit API transport and Actions summary
formatting; pinned `actions/download-artifact` restores the verified run's exact
artifact. Our code supplies the authorization/SHA/issue predicates and journal
binding. It no longer shells out to `gh` for API transport or artifact download.
Both new action pins run Node 24 and require Actions Runner >=2.327.1; this workflow
uses GitHub-hosted Ubuntu, not an unqualified self-hosted image. Guard tests execute
the actual JavaScript against synthetic Octokit responses with no credentials.
The summary requires a successful current controller outcome; restored historical
readiness cannot label a failed resume as a new acceptance.

The workflow has **read-only** contents/issues/actions permissions, no `secrets`
bindings, no publishing/merge/deployment jobs and no provider SDKs. Its short-lived
GitHub token is available only to trusted managed actions for metadata/artifacts,
not to fixture roles. Contexts are an explicit allowlist without process env,
untrusted issue text or implementation transcripts. These are controlled Python
fixtures in one process, **not an OS sandbox for arbitrary plug-ins**. Never load
untrusted Python or execute candidate code in this controller.

Only one fixed synthetic path per issue is admissible. Traversal, absolute/Windows
paths, alternate data streams, control files, dot-env files, out-of-scope paths,
and symlink components are rejected. Changes remain data in the run journal;
there is no arbitrary shell/patch evaluator. Output directories are selected by
the maintainer/workflow, never by issue text or a provider. A crash can leave a
lock: verify its owner has stopped before manually removing it. Never auto-delete
a possibly live lock or reset repair counters.

## Later owner activation — deliberately separate

Do not add keys merely to pass this PR. Actual OpenAI/Gemini execution first needs:

* Human-reviewed integration of the official Codex action and Gemini CLI action,
  with isolated tools/runners and the canonical policy/trusted-base config. Do not
  build parallel model clients. Prefer supported credential proxies/workload
  identity; no raw provider key may reach candidate code, prompts, logs or the
  artifact publisher. Fixture `synthetic` identity flags are not authentication.
* Protected GitHub environments such as `ai-implementation` and `ai-review`, with
  reviewed actor/ref restrictions and project-specific OpenAI/Gemini bindings.
  Enter values in the secure environment UI only. Google access alone does not
  establish Gemini API billing/quotas; review GCP WIF if supported by the chosen
  adapter. No Alpaca/Massive/SEC-auth/deployment/admin keys belong in either job.
* Qualify maintained issue-to-PR plumbing before implementing publication. Current
  OpenHands `github-issue-to-pr` substantially overlaps this need, but gives the
  coding agent a write-capable token and publication responsibility. Adopt only
  after a supported configuration/integration preserves our separate publisher,
  exact-base controls and durable caps. Do not fork its scheduler into this repo.
* Exact monthly and per-run dollar/token/time limits, an authoritative cross-run
  spend/reservation ledger, idempotency/ambiguous request recovery, price/version
  snapshots and shutdown behavior. Max repairs stays 2 across resumes/retries.
* Separate GitHub publication/review-comment jobs with short-lived narrow tokens,
  typed validated outputs, current-head checks and no candidate execution on the
  publisher. Existing secretless PR CI, independent model review, human approval
  and manual merge remain mandatory. No ruleset bypass or protected-branch token.

The current `provider_activation_enabled=false` configuration rejects real
providers; supplying a key cannot activate them. Do not flip it without that
reviewed implementation. FMBH remains unresolved and untouched; this bootstrap
does not authorize the next scientific task, data calls, paid procurement or any
trading. Hosted GitHub access/CI must be reported separately from local acceptance.
