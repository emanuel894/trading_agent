# Issue #12 checkpoint

Branch: `research/issue-12-event-evidence-contract`
Base: `feat/alpaca-paper-foundation` at `b5b06af7a876ebb4c7fc9ab6f63cbaed9ef2aafe`.
Mandate: https://github.com/emanuel894/trading_agent/issues/12

## Resume safely

Read `AGENTS.md`, trusted-base `AI_PROJECT_POLICY.md`, this checkpoint and the
issue snapshot before continuing. Work only on this branch. PR #10 is context
only; never push its branch. No alpha, candidate #2, registrations/amendments,
paid/provider/model calls, secrets, broker actions or ingestion platform.

## Progress

- Read Issue #12, repository policy, ADR 001, Amendment 005 and PR #10 architecture
  context (remote PR head `4dd7703f429df01a6f7e67912294ec26e93b4ad0`).
- Created the dedicated branch from the fetched remote base. Existing checkout
  retained as required by repository policy; no worktree created.
- Design-only deliverable: portable envelope plus source matrix/admission,
  correction, entity and baseline rules; separately registered future experiment
  proposal. No production implementation is planned.
- Next: capture current public documentation; write artifacts; verify schema,
  source integrity, protected-file scope and existing fixture suite/demo; obtain
  independent review; push and open a draft PR targeting the base branch.

## Operational notes

- Initial shell fetch without network permission failed to reach the session
  proxy. Explicit network-enabled execution succeeded. Preserve proxy settings.
- FMBH remains UNRESOLVED. This design does not clear acquisition or qualify any
  historical event feed by mere API reachability.
- Authoring agent: Codex GPT-6, HIGH reasoning requested. No external model API
  will be called. Exact backend build is not exposed.
