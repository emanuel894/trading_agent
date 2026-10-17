# Issue #5 — real automation activation qualification

Status: **PAUSED_BUDGET**. Real acceptance has **not** run. This branch records
the safe, completed qualification work and the exact activation blockers; it
does not implement or claim a functioning real-provider loop.

Issue: [#5 — Activate real autonomous agent loop](https://github.com/emanuel894/trading_agent/issues/5).
Trusted base: `42013189c47a48014f0ad8658a868f6caa6a68f5`,
`feat/alpaca-paper-foundation`. This includes the merged Issue #3 guard harness
and de-duplication review. The issue snapshot, actual observations and source
hashes are recorded beside this document. Canonical rules remain in
[AI_PROJECT_POLICY.md](../../AI_PROJECT_POLICY.md).

## Why execution stops before a provider call

Issue #5 requires: “If cost state is unavailable, ambiguous, or exhausted:
`PAUSED_BUDGET`.” This environment cannot verify any authoritative monthly
balance/reservation state, exact per-run cost/token/time caps, price snapshot or
provider billing enforcement. Approximately $50 is a target in the issue, not
an observed configured hard limit. No provider call, retry or paid acceptance
attempt is allowed on this evidence.

Only the existing GitHub binding is visible by name in this runtime. No OpenAI,
Gemini or Google workload-identity binding was observed here. That does **not**
prove protected GitHub environments lack credentials. Both GitHub GraphQL issue
access and REST protected-environment listing were denied by the runtime proxy.
Git fetch works; API permission and environment protection remain unverified.
The public issue page provided the exact requirements, without a private token.
No secret value or credential file was inspected or copied.

Consequently no protected environment, billing setting, secret, GitHub App,
workflow trigger or repository rule was changed. The existing
`provider_activation_enabled=false` and zero-cost synthetic controller remain
unchanged. A key alone cannot activate that controller. We do not treat a local
Codex executable, this coding session, a fixture review or a provider's soft
budget alert as the requested real Codex/Gemini acceptance.

The [routing policy](routing_policy.json) is a **non-executable policy draft**:
allowed task/risk labels, replaceable role bindings and required audit fields.
No workflow consumes it yet. Null model IDs and budget bindings mean unqualified,
never provider defaults or unlimited spend. No router, provider client,
scheduler, billing ledger or generic issue-to-PR framework was built.

## Maintained-tool qualification

Exact revisions were resolved again for Issue #5, then current source, schemas,
licenses and relevant examples were fetched at those revisions. Sources were
inspected, not installed or executed. See [source inventory](upstream_sources.json).
These are inspected commits, not approved deployed release/runtime versions.

| Component | Exact inspected revision | Decision and source-grounded reason |
| --- | --- | --- |
| `openai/codex-action` | `a8d8be6ee028bea4525bc722d16f36687b408c81` | INTEGRATE for implementation. `action.yml` exposes model, output schema, permission profile and privilege strategy; `docs/security.md` describes key/procfs risks, trusted config and a fresh publisher job. Use its supported proxy/runtime rather than custom OpenAI clients. Apache-2.0. |
| `google-github-actions/run-gemini-cli` | `387c8ddb7a72078825da941758b811b9153c71e8` | INTEGRATE for independent review, subject to isolation qualification. Action supports explicit CLI/model/settings and WIF/Vertex/API-key inputs. Its review example grants PR/issues write, trusts the workspace and installs an extension; do not copy those privileges. Apache-2.0. |
| `peter-evans/create-pull-request` | `bd09a93810788ce61d2d5fb7d6b221b9b4a4aab7` | INTEGRATE for a fresh publisher, not inside a model job. Schema supplies fixed branch/base, draft PR, scoped token inputs and actual head SHA output. Source supports branch updates/PR lifecycle. It does not enforce our registered exact base, allowed paths or spend/repair state. MIT. |
| `obra/superpowers` | `bb92a77741419a4ab5f06e711a283343f1ada0c3` | INTEGRATE planning/TDD/scoped review process. Its five-round default does not override our two-round maximum; no extra final-review repair allowance. Existing isolated checkout and human merge policy override worktree/merge defaults. MIT. |
| `OpenHands/extensions` | `d05780951082d4d83f785cb1d4c7f2be6d1c14a5` | OPENHANDS_DEFER for this pilot; bounded qualification below. Do not fork its worker or build a substitute lifecycle platform. MIT. |
| `OpenHands/automation` | `bc4cca7c7e2eab5cb7d0ff671bec5dd113d3e2c2` | DEFER service deployment. Real dispatcher/run storage exists, but package 1.20.1 is beta and adds service/database/sandbox operations without resolving the worker publication boundary. MIT. |
| `BerriAI/litellm` | `b5037f28d172f6f6375ba3d08dcdf2c10deb8d2d` | DEFER gateway deployment, not reject its budget functionality. It already implements reservations/reconciliation and fail-closed backend-error handling. Unknown/nonpositive cost estimates return no reservation and fall back to read-time enforcement, even through the inspected reservation function's fail-closed setting. Qualify exact priced routes, proxy compatibility, persistence and ambiguous-call behavior before relying on it. MIT outside `enterprise/`; enterprise terms separate. |
| Existing pinned GitHub actions | Pins retained unchanged in `.github/workflows/autonomous-dev-dry-run.yml` | KEEP/INTEGRATE checkout, Octokit, concurrency and artifacts; no replacement transport client. Existing inventory and digest-warning limitation remain applicable. No new workflow or moving action reference was added. |

Current official action HEADs and OpenHands revisions match the previous audit;
this is fresh ref/source inspection, not an assumption that past findings still
apply. Failed guessed LiteLLM documentation paths are recorded as unavailable,
not evidence that functionality is absent. The reservation implementation itself
was inspected. No stars, promotional claims or unexecuted benchmarks establish
tool correctness or model quality.

### One bounded OpenHands qualification

**Outcome: OPENHANDS_DEFER.** The inspected integration cannot be adopted
unchanged under our separate-publisher policy. This is not a claim that the SDK
can never support a compliant architecture, or a reason to fork it.

| Required boundary | Observed code / result |
| --- | --- |
| Coding worker without broad GitHub write token | Not demonstrated by the shipped issue-to-PR path. `skills/github-issue-to-pr/README.md` grants contents/PR/issues write and recommends workflow scope. `worker.py::_workspace_instructions` names the agent's GitHub token; `_prompt` tells it to push/open/relabel PRs. Legacy `main.py::_build_secrets_payload` supports empty `AGENT_SECRET_NAMES`; the current worker dispatcher instead resolves secrets from an agent profile. Neither path demonstrates a complete supported patch-only worker with separate publication. |
| Fresh separate publisher | Not supplied by that worker. Agent publication and fallback script publication are part of its integration. Do not add a write token merely to make it work. Use a maintained publishing action on a fresh runner after output validation if later qualified. |
| Exact base/head admission | Partial capability exists: worker fetches base SHA, reads review status at exact PR head and names that head in revisions. Prompts to clone/branch do not enforce our registered checkout/policy SHA or revalidate publication atomically. Project admission predicates remain necessary. |
| Two repairs and budget receipt across resumes/retries | Shared `skills/github/scripts/agent_conversation.py` deduplicates subject/delivery, tracks provenance and caps error retries at two **per delivery**. A new delivery resets that counter; it is not a global PR repair cap or combined monthly budget reservation. Lifecycle state is valuable but not proof of these project limits. |
| Exclude candidate-controlled instructions/config/plugins | Legacy secret/MCP allowlisting is useful; current worker profile isolation is unverified. The coding workspace flow does not prove trusted-base-only instruction/config loading, hook exclusion or read-only review configuration. No adversarial runtime test was run; unresolved remains unresolved. |

No OpenHands profile, server, poller, provider binding or automation was created.
Do not turn this deferred integration into an `OPENHANDS_SECURITY_BOUNDARY_BLOCKER`
for all alternatives: official runners plus maintained publishing actions remain
the preferred simpler pilot path once its own prerequisites are qualified.

### Specific budget and publication limits

LiteLLM's `litellm/proxy/spend_tracking/budget_reservation.py` is more than a
post-hoc spend counter: it reserves estimated maximum request cost, renews leases
and reconciles/rejects according to configuration. However,
`reserve_budget_for_request` defaults `fail_closed_budget_enforcement` to false,
returns no reservation without counters/model, and explicitly returns none when
the estimated cost is unknown/nonpositive. Merely installing the gateway or
setting a virtual-key budget does not prove all Codex Responses/Gemini requests
and retries meet this issue's unknown-cost pause contract. Do not custom-build a
ledger before qualifying this maintained alternative, but do not call it a hard
cap without demonstrated coverage either.

`create-pull-request` removes substantial branch/PR code. Its base input names a
branch, and its code can update branches; a successful action is not proof of
our exact admitted base/head. A separate trusted guard must validate actual
committed bytes, issue scope and current SHA before any mutation, then record
the action's returned head and re-fetch actual PR state. Ambiguous publication
must block further publication/provider work pending reconciliation, not trigger
another fresh PR or reset repairs. A
GitHub App binding in the publisher must be narrow and unable to merge/bypass
protected branches; normal `GITHUB_TOKEN` publication may not trigger ordinary
PR CI, so that behavior needs an observed acceptance test.

Do not put a publisher token after a model step on the same runner. No model
output may run as shell, workflow YAML, hooks or configuration in a publisher.
The artifact downloader's known digest-mismatch warning also still requires a
qualified hard receipt/byte-integrity boundary before privileged publication.

## Resume prerequisites and exact acceptance

Continue this issue when GitHub API access works through the supported runtime
route. Do not extract proxy credentials or request a broad PAT. Then:

1. Verify/create protected `ai-implementation` and `ai-review` environments with
   reviewed actor/ref restrictions. Bind provider access only through secure
   environment settings; prefer the Codex credential proxy and Google WIF where
   qualified. Record protection metadata without secret values. No broker,
   acquisition, deployment, merge or administration credential enters a model
   job. Keep publication on a separate runner with narrowly scoped credentials.
2. Select available exact provider model and CLI versions. Sol/Astra are policy
   classes, not invented public API model IDs. Record actual IDs, reasoning
   support and prices. Substantive implementation defaults to Sol-class/High;
   GREEN may use a cheaper/medium path. RED escalation requires a documented
   architecture/science/security blocker and cannot grant scientific authority.
3. Establish an authoritative combined monthly hard cap near the $50 target,
   exact per-run cost/token/time caps, durable pre-call reservations and failure
   reconciliation. Verify the configured provider/gateway enforcement, not a
   dashboard alert. Unknown cost, interrupted/ambiguous usage or backend outage
   means PAUSED_BUDGET. Count failed attempts and both providers. No cap increases
   or new task/PR identity to reset limits.
4. Qualify the official model jobs and maintained publisher on secretless test
   inputs before binding paid credentials. Trusted policy/workflow/config must
   come from the protected base; PR hooks/instructions/plugins are data. Static
   Gemini review must have no candidate execution, shell/write/MCP publication
   tools or candidate-controlled settings. Capture a bounded receipt with exact
   issue hash/base/head, model identity, findings, usage and unknowns. Never use
   fixtures as proof of real isolation or independent model review.
5. Implement only the small remaining project guards, after documenting concrete
   upstream gaps: exact SHA/scope admission, trusted policy/receipt binding,
   global repair budget and fail-closed readiness. GitHub remains the durable
   bus; no new provider client, scheduler or conversation engine. Enforce global
   implementer concurrency 1 and reviewer concurrency 1, max two repairs across
   all resumes/retries, no recursive workflows and no auto-merge. Reconcile a
   failed/interrupted run from durable evidence before any further call/write.
6. Run one real harmless coding issue, confined to a synthetic file, through
   Codex, separate branch/PR publication, mandatory secretless Foundation CI and
   fresh Gemini review. Exercise repair once (a disclosed injected finding is
   allowed), stale-head rejection, second-repair limit and interruption recovery.
   No human copy/paste between providers. Persist all SHAs, actual model/usage,
   costs, CI, findings, counters and final READY_FOR_HUMAN. Only that observed
   result permits `REAL_AUTOMATION_READY_FOR_HUMAN`; human merge stays mandatory.

These are remaining prerequisites, **not completed activation steps**. Acceptance
items 1–10 in Issue #5 remain NOT_RUN. Existing local tests establish regression
safety only. The issue remains open. Even after acceptance, this task does not
start FMBH, advance candidate #2, spend acquisition calls, amend science or enable
Paper/Live orders. Those tasks retain their separate gates.
