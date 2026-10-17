# Cloud agent development plan — 2026-10-17

**Proposed, not deployed.** GitHub holds code, issues, PRs, registered protocols,
manifests and the review trail. Private versioned storage holds licensed raw data
and large artifacts. Agents are workers on bounded issues; GitHub controls and
humans retain promotion/merge authority. No workflow, repository setting, secret,
GitHub App, review bot or protected-branch rule was installed by this audit.

The scientific contract remains in [AI_PROJECT_POLICY.md](AI_PROJECT_POLICY.md)
and its registered references. This design cannot change FMBH's UNRESOLVED state,
authorize the remaining 58 Massive requests or enable trading.

## 1. Pick two providers, with a measurable reason for each

| Role | Choice | Authority and value | Evidence/limits |
| --- | --- | --- | --- |
| Bounded implementer | Codex Cloud for supervised issue work; `openai/codex-action` for a later reproducible Actions route | Read repository, edit an allowed feature/task scope, run fixture tests, produce a patch/feature PR. Existing prepared environment reduces setup cost. | CLI/action source is Apache-2.0; Cloud/model service terms are separate. Cloud and action invocations are the same role, not independent reviews. No automatic deployment or trading authority. |
| Independent reviewer | Claude Code via `anthropics/claude-code-action` | Inspect the exact PR diff and surrounding source from a fresh, restricted context; find bugs, scientific regressions and unsafe changes. Produce findings, not fixes/merge commands. | MIT action wraps a commercially licensed CLI/service. Independent model context improves diversity but does not eliminate correlated mistakes. Human acceptance and tests remain required. |
| Deterministic verifier | Existing GitHub Actions tests plus later trusted guard checks | Run full suite/demo on supported OS/runtime, validate protected-artifact/policy constraints, attach exact-SHA results. | Not an AI vote. No provider/broker secrets; do not execute candidate code in a credential-bearing review job. |
| Release/merge authority | Human maintainer | Approve science/policy changes and protected-branch merge after current checks/review. | No AI auto-merge or ruleset-bypass permissions initially. |
| Reserve | Gemini CLI / `google-github-actions/run-gemini-cli` | Offline bake-off or replacement for one existing role if it creates measured value. | No standing third reviewer, secrets or billing configured. GCP Workload Identity Federation is an available option if later adopted. |

The audit inspected commit-pinned action schemas and security documentation;
see [the main audit](BUILD_VS_ADOPT_20261017.md#source-index) and
[source inventory](audit/20261017/upstream_sources.json). Pin **approved full
action SHAs, CLI versions and model identifiers** when implementing. Do not copy
moving `@main`, `@v1`, `latest`, preview/nightly or old README inputs blindly.
The inspected Codex action supports `permission-profile`; do not also supply its
legacy `sandbox` input. Use its documented privilege reduction as well as command
sandboxing. Gemini's inspected HEAD is nightly; use a qualified release if tried.
Use Linux for credentialed agent runners: the inspected Codex action requires its
unsafe strategy on Windows. Windows remains a secretless test-matrix target,
not a reason to weaken agent sandboxing. Keep the engine's Python.NET runtime and
the CLI/action Node/Bun runtimes isolated from the application Python environment.

Reviewer independence means a distinct Anthropic model/backend and a fresh
context, not merely a second CLI name routing to the implementer's model. Give
the reviewer the PR, source and CI evidence without the implementer's private
reasoning transcript. Record provider/model identity so this can be checked.

## 2. Concrete end-to-end flow

1. A maintainer opens a bounded issue with acceptance criteria, allowed paths,
   prohibited changes, required tests, risk category, base branch/SHA and a finite
   model/time budget. Research issues name the registration/evidence hashes and
   whether a human-reviewed amendment is needed. No holdout results in prompts.
   A maintainer authorizes the task through Cloud or a `workflow_dispatch` with a
   numeric issue ID and exact base SHA. Public comments/labels alone do not grant
   arbitrary users access to paid runs.
2. Codex starts from that exact base in the existing isolated checkout. It reads
   the trusted canonical policy, implements the issue and runs fixture tests.
   No live/broker tools, data acquisition keys, repository administration or
   deployment credentials exist in its environment. Network access is limited to
   required development/model destinations. Dependencies are prepared from
   reviewed declarations before arbitrary candidate code is executed.
3. Persist the result on `ai/issue-<number>-<short-base-sha>` and open a draft PR
   to the selected base. Initial Cloud use can have the maintainer publish the
   branch/PR through the product. For automated publication, use the separated
   publisher design below; never grant the coding shell a protected-branch token.
   The PR includes issue, base/head SHA, model/tool versions, summary, precise
   validation, evidence/registration changes, costs and limitations.
4. Ordinary `pull_request` CI executes the full existing suite and synthetic
   demo on Ubuntu and Windows/Python 3.13 with `contents: read`. No broker/model
   provider secrets are available. Tests run real candidate code in this
   secretless job. Fork contributions can run these checks without gaining
   credentialed agent jobs.
5. The maintainer requests an independent Claude review with exact PR number,
   base SHA and head SHA. A trusted control job re-fetches PR metadata and creates
   an immutable review bundle containing the diff, relevant source, trusted-base
   policy and CI evidence for that head. Source is read as data; do not check out
   and run PR scripts/hooks/config in a privileged review job. Review focuses on
   safety/science first, then implementation, missing tests and operational risks.
6. A fresh review-only runner invokes Claude on that bundle with read-only tools,
   no shell/code execution, no editing tools, no broker/data keys and no write
   GitHub token. Freeze provider/model/prompt versions and a token/turn/runtime
   budget. A finding includes file/line, severity, concrete trigger/consequence,
   supporting source/test, and confidence/unknowns. It must distinguish a verified
   defect from speculation. No finding is not a correctness certificate.
7. A separate publisher validates the structured review output and posts it as
   a comment/check for the **reviewed head SHA**. It never executes model-produced
   commands or treats review text as workflow YAML. Its short-lived token has
   only the narrow comment/check permissions. A model does not submit a human
   approval or merge. If the head changed, mark the result stale and request a
   new review; do not transfer a green check to new code.
8. Codex addresses confirmed findings in the same PR within its task budget.
   Any new commit invalidates the reviewed-head association and reruns CI/review.
   Human triage resolves disagreements and unsupported findings explicitly.
   Required human approval and fresh mandatory checks precede a manual merge.
   Registered science or security-policy changes require focused maintainer
   review even when all tests pass. A provider outage produces an incomplete
   review, not a passing check or a silent fallback to the implementer model.

Use concurrency groups per issue/PR to prevent competing writers and duplicate
paid reviews. Cancel superseded runs. Initially allow at most one implementer and
one review run per PR at a time; cap repair loops (proposed: two automatic rounds,
then human triage). Additions to scope become a new issue or an explicit update.

## 3. Separate model work from GitHub write access

For a later Actions implementation route, the safe data path is:

```text
trusted dispatch (issue ID + base SHA)
  -> read-only GitHub fetch / secretless checkout
  -> Codex isolated editing/test process
  -> bounded structured patch output
  -> NEW publisher runner: validate + apply to exact base, no candidate execution
  -> feature commit/PR
  -> secretless PR CI
  -> NEW Claude static review runner with trusted-base policy
  -> NEW review publisher: structured findings/check on exact head
  -> human approval + manual merge
```

Do not place a credential-bearing publisher after an agent on the same runner.
The Codex security document specifically warns about background processes,
modified Actions code and Git hooks. Prefer its action as the final step of the
model job. For bounded text changes, a schema-constrained final output containing
the patch, base SHA and declared changed paths can be passed through job outputs
to a fresh publisher, with an enforced size limit below GitHub's output limit.
The publisher checks exact-base application and computes the committed diff
itself; model claims about files/tests are not trusted. Larger/binary patches
fall back to supervised Cloud publication rather than unsafe shell handling.

The publisher must reject paths outside the issue allowlist, `.git` paths,
symlinks/submodules, path traversal, credential files and unauthorized control
changes. Science registrations, ledgers, provider instructions, `.github/`, agent
config/hooks and dependency changes require an explicit maintainer-reviewed task
scope; generic issue agents cannot grant that scope themselves. Do not use shell
`eval`, interpolate PR text into scripts or run candidate hooks/build scripts.
Use API/structured arguments and a clean publisher image; reject stale base or
unexpected branch state. PR CI verifies the actual committed tree.

A repository-scoped GitHub App token does **not** inherently restrict writes to
one branch. Branch/ruleset protection, no bypass role, plus publisher-side branch
and path checks enforce the intended scope. Keep the long-lived App private key
outside all model jobs; mint short-lived installation tokens only in trusted
publisher jobs. Never use an unrestricted personal access token as a shortcut.

## 4. Permissions and secrets

| Job/service | GitHub capability | Other credentials | Forbidden capabilities |
| --- | --- | --- | --- |
| Intake/fetch | Metadata/issues/contents read on this repo | None | No writes, administration or broker calls |
| Codex model job | Read-only checkout; no GitHub write token in model tools | One project-scoped, budget-limited model binding via supported protected runtime/proxy | No App private key, acquisition keys, Alpaca Paper or Live keys, ruleset bypass or cloud deployment |
| Feature publisher | Short-lived contents/PR write on this repo; no administration/workflow permission | GitHub App binding only | No models, candidate execution, protected-branch push/merge or trading |
| PR test job | `contents: read`, checkout credentials not persisted | None | No provider, acquisition, broker or publishing secrets |
| Claude review job | Prefer no GitHub token after bundle construction; otherwise read only | Separate budget-limited Anthropic project binding | No shell/candidate execution, write tools, trading, data acquisition or publisher token |
| Review publisher | PR comment/check write as needed; contents read if required | Short-lived scoped GitHub App token | No contents write, model invocation, merge or executing review text |
| Owner acquisition | Outside coding/review; governed by registered capture plan | Only the approved source/rights binding and request budget | No Live trading and no new scientific authorization inferred from possession of a key |
| Future Paper executor | Separate host/environment/account writer | Paper keys only after its own gate | No Live keys, autonomous code updates or coding agent access |

Use protected GitHub environments for model jobs, actor allowlists and spending
limits. Where supported, use a managed credential proxy or secret manager with
workload identity so tools do not receive raw keys. Codex action includes an API
proxy; do not assume identical protections in Claude/Gemini wrappers. If a raw
provider key is needed in the trusted API client, isolate it from child tool
processes/filesystem/proc access, restrict egress and keep the key project-scoped
and revocable. Read-only filesystem flags and `allowedTools` alone do not prove
secret isolation; validate the actual runner boundary before activation. Avoid
host-wide credentials, writable shared caches and broker-connected self-hosted
runners. API budget abuse remains a residual risk even with correct isolation.

Alpaca Live credentials must never be created, bound or stored in coding/review
environments, including repository-level Actions secrets inherited by such jobs.
The same exclusion applies to local `.env`, cached SDK files, MCP configuration,
review attachments and runner images. Repository gitignore rules are useful but
do not enforce this boundary. No MCP trading server belongs in these jobs.

## 5. Trigger and untrusted-content controls

* Begin credentialed work with maintainer `workflow_dispatch`, reading workflow,
  prompts, policy and agent settings from a protected base. Revalidate actor
  access, exact repository/PR membership and current base/head through GitHub.
* Use `pull_request` for secretless candidate CI. Initially do not use
  `pull_request_target`, privileged `workflow_run` or broad `issue_comment`
  execution to run a PR checkout. Future event-driven automation must preserve
  the same trusted-control/data-only split and explicit authorization.
* Do not set `allowed_bots: '*'`, `allowed_non_write_users: '*'`, `allow-users:
  '*'` or analogous broad bypasses. A bot-authored PR can be reviewed after a
  maintainer dispatch without granting arbitrary bots authority to start runs.
* Ignore PR-controlled `AGENTS.override.md`, nested instruction files, hooks,
  plugins, MCP endpoints, `.claude`, `.gemini`, `.codex` configuration and modified
  workflow files as execution configuration. Review them as code changes using
  trusted policy. Disable automatic discovery of candidate-side plugins/hooks.
* Treat issue/PR text, source comments, SEC filings and retrieved web pages as
  potentially adversarial. Static review still faces prompt injection; constrain
  tool capabilities and token budgets even after human dispatch. Never expand
  untrusted strings directly into shell commands.

The inspected Claude action restores certain instructions/config from the base
and describes subprocess scrubbing, but explicitly calls some defenses best
effort. Do not mistake wrapper safeguards for a complete sandbox. The inspected
Codex action likewise separates permission profiles from process privilege
reduction. Verify the exact pinned versions used at rollout.

## 6. Mandatory checks and GitHub protection

Preserve the existing `Foundation tests` matrix. Confirm the actual emitted
status names in GitHub before configuring required checks; expected matrix jobs
are `tests (ubuntu-latest)` and `tests (windows-latest)`. Require a trusted
independent-review check bound to the current PR head, plus one human maintainer
approval, dismissal of stale approvals and resolution of blocking discussions.
Require branches to be current or test the actual merge candidate under an
equivalent protected mechanism. Agents and their Apps get no bypass list entry,
force-push permission on protected branches or merge authority. Human merge only
initially. Check-name spoofing is addressed by restricting required check sources
to the intended GitHub App/workflow where GitHub supports that control.

Add trusted guard checks in a separate implementation: protected research hashes,
no unsafe flag/endpoint introduction, registration-linked changes, no secret/raw
licensed data additions, action pins and policy-entry consistency. Obtain guard
logic from the trusted base, so a PR cannot make its own checks vacuously pass.
Do not use a model's summary, an edited workflow or a skipped zero-test job as
test evidence. Code touching the guard, tests, CI or registrations requires human
review beyond check success. Policy/checks cannot completely replace code review.

Provider outage, budget exhaustion, unavailable CI or an unexplained test failure
blocks completion. Use a human-documented exception process only where the owner
explicitly authorizes it; no AI-generated exception or automatic fail-open.

## 7. Audit record and cost/value measurement

For each run retain: issue/PR/run ID, base/head/merge-candidate SHAs, policy and
prompt hashes, provider/model/tool/action versions, allowed tools/network scope,
start/end/status, token/API usage, wall time, patch/review hash, CI links,
structured findings, human disposition and final merge SHA. Record retries and
failed runs. Store references to evidence/manifests without leaking underlying
licensed bytes or secrets. Private logs need access controls and a defined
retention policy; do not enable full raw transcripts by default.

Proposed initial combined model cap: **$50–150/month**, subject to owner budget,
actual service prices and hard per-run/turn limits. This is a proposed ceiling,
not a quoted price or purchased subscription. Separate provider charges from
GitHub runner/storage costs and research LLM/data expenses. No provider billing
was configured or model called in this audit.

Pilot on 5–10 bounded issues without changing scientific criteria. Measure
accepted implementation rate, regression/escape defects, maintainer minutes,
confirmed reviewer findings, false-positive burden, elapsed time and cost per
accepted PR/confirmed defect. The second model earns its role if the review's
confirmed findings or reduced human review time justify its cost. Do not measure
success by number of agents, comments, generated lines or claimed alpha.

Gemini gets no standing role unless an offline blinded comparison on the same
approved code-review/implementation tasks demonstrates at least comparable
accepted quality at lower total cost or material additional confirmed findings.
If so, replace a role first; add a third only if measured marginal benefit
exceeds complexity/cost. Freeze comparison criteria before looking at outcomes.

## 8. Rollout and explicit exclusions

First review the canonical policy and this design. The **single recommended next
implementation milestone remains the FMBH structural-source qualification spike**
defined in the main audit. Agent automation is a later bounded development-controls
task; it does not get ahead of that scientific blocker or justify data calls.

After that, qualify pinned actions and isolated runners with synthetic issues,
exercise stale-head/provider-failure/path-escape and secret-isolation rejection
cases, then pilot two providers with manual dispatch and human merge. Only after
measured benefit should authorized event-driven invocation expand. No autonomous
merge, paid data procurement, Live credentials, agent trading, framework migration
or ongoing trading service is included in this plan.
