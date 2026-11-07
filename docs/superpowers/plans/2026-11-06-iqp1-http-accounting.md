# IQ-P1 durable transport accounting implementation plan

> **For agentic workers:** Use superpowers:executing-plans inline, then one fresh independent code reviewer.

**Goal:** Close the demonstrated process-local HTTP accounting gap without launching the blocked real-data pilot.

**Architecture:** Extend ReadOnlyHTTP with an optional fixed-pilot budget backed by append-only EvidenceStore records. Reserve attempt/body allowance durably before opening a request; settle only against its persisted HTTP response. Interrupted/ambiguous attempts remain charged and block another attempt. No new collector, storage engine, private runner, resource sandbox or credentials path.

**Tech stack:** Existing Python standard library, EvidenceStore transactions and unittest.

**Spec:** Owner's IQ-P1 Real-Data Boundary Pilot mission received2026-11-06; canonical policy; IQP1_SOURCE_PLAN.md; PR55 proposal/PR56 CP4 plan. Base5f8b850548e2f7786814086d5350a72a19d87459. PR59/60 remain untouched draft dependencies outside this branch.

## Global constraints

- Fixed pilot accounting namespace; max128 attempts,2,000,000,000 retained body bytes,30-minute pre-call deadline; tests may use stricter limits.
- Explicit one-time initialization; reopening cannot reset limits, spending, deadline or pending reservations. No new pilot identity argument or reset API.
- Serialize reservation/settlement through existing store transactions; one pending request at most. Retry/failure/pagination calls use the same budget.
- Existing local transport limits remain effective and stricter where applicable.
- This closes accounting only. It does not supply4GiB physical quota/reserved space,2GiB memory, a hard30-minute process watchdog, approved sole private ledger or credential separation.
- Actual attached context: coding environment, no acquisition bindings; observed cgroup memory.max8GiB. No verified private quota/watchdog. **No market/source requests may launch.** Do not obtain or read credentials, restore archives or repeat accepted probes/tests.
- Preserve all scientific protocols, sample dates, quote/exit semantics, broker flags and PR59/60. No acquisition, inference, returns, deployment or merge.

## Review focus

1. Retries/failures/new HTTP objects must not reset cumulative counters.
2. Crash before/after network persistence must retain reservation and prevent unsafe retry.
3. Body-byte refunds need matching persisted response evidence, not caller assertions.
4. Pending reservations and transactions must enforce one request at a time across connections.
5. Error responses and oversize reads must respect remaining retained-byte allowance.

## Task 1: Narrow accounting hook

**Files:** agent/iqp1_http_budget.py; modify agent/audit_http.py only to attach/reserve/settle the budget; tests/test_iqp1_http_budget.py; one result/checkpoint document.

**Interfaces:** IQP1HTTPBudget.create(store, stricter optional limits) initializes once; IQP1HTTPBudget(store) reopens; reserve(url, max_bytes)->(reservation_id, allowance); settle(reservation_id,http_record_id); snapshot() returns accounting metadata. ReadOnlyHTTP(..., budget=None) preserves existing callers.

- [x] Write restart/retry/failure/pending/settlement/body-cap/concurrency/deadline tests using explicit synthetic fake transport and temporary stores; observe initial missing-feature failures.
- [x] Implement append-only accounting and minimal transport hook; do not implement a substitute private acquisition runner.
- [x] Execute the new enforcement tests and required regression suite/demo, measuring results without opening performance artifacts.
- [ ] Obtain one exact-head independent review; publish a foundation-based draft PR with required Ubuntu/Windows CI.
- [ ] Preserve DATA_BLOCKED and0 actual pilot attempts/bytes; report the concrete private-context/resource gates. Source-only pre-close windows are compatible with unresolved post-close coverage only with executable admission prohibited; do not amend exit rules.
