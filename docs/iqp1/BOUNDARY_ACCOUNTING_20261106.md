# IQ-P1 boundary pilot: durable HTTP accounting, acquisition stopped

Base: `feat/alpaca-paper-foundation@5f8b850548e2f7786814086d5350a72a19d87459`.
Branch: `feat/iqp1-durable-http-budget-20261106`; resulting exact head/review/CI
are bound in the draft PR receipt. This branch is independent of draft PR59/60,
which remain unchanged/unmerged, and does not merge draft PR55/56.

## Reuse first; concrete missing capability

Reused `SIPSource.pages` (agent/audit_market.py), `ReadOnlyHTTP`
(agent/audit_http.py), `EvidenceStore` transactions/verification
(agent/audit_store.py), existing quote/bar validators and immutable contracts.
Accepted PR51 qualification, PR56 archive restoration/native replay, PR55's
unchanged IQ-P1 proposal, PR56's pinned CP4 full-year plan and November6
IQP1_SOURCE_PLAN.md remain authoritative within their existing scopes.
No accepted native/source/entitlement/restore test or framework audit was rerun.

The inspected transport initialized request and body counters in each Python
object; creating another object reset them. It also read error bodies without
respecting the remaining byte allowance. Those are demonstrated enforcement
gaps, distinct from the still-blocked private execution context.

The new `IQP1HTTPBudget` uses existing append-only EvidenceStore records and
transactions. The transport receives it via optional `budget=`; existing callers
are unchanged. The fixed accounting namespace has no new-identity/reset API.
Creation is explicit and one-time; reopening reads existing limits, deadline,
attempts, retained bytes and outstanding reservations. Tests may choose stricter
limits; the class refuses limits above128 attempts/2,000,000,000 body bytes/1800s.

Before each HTTP open, a committed reservation consumes an attempt and worst-case
retained-body allowance. Retries and pagination share that ledger. A response
settles only against matching persisted HTTP evidence and actual hashed bytes;
ledger replay also validates the response reference/size. An interrupted attempt
stays fully charged and prevents another request until a matching persisted
response can be reconciled. No guessing, retry-until-green, refund-by-assertion or
automatic release of ambiguous reservations. Reservations serialize through
BEGIN IMMEDIATE across connections. Existing stricter local request/byte limits
and transport retry limits remain effective. Error-body reads now respect the
reserved remaining retention allowance.

## Exact limits of this enforcement

**This is accounting hardening, not a launch-ready pilot or private runner.**
One approved sole ledger/path and all egress must be bound by the private
acquisition context. A fresh unrelated store is not an authorized new pilot.
The default legacy transport without budget remains unchanged and must not be
used to execute this mandate. The helper does not authenticate an operator or
enforce an external context's filesystem/process privileges.

The persisted30-minute deadline prevents starting further HTTP attempts after
expiry and rejects clock regression; it does **not** kill an already running
process/read or substitute for a hard watchdog. Retained HTTP-body accounting is
not a wire-byte meter, physical disk quota, reserved-free-space guarantee or RAM
limit. It does not enforce12 logical packets or1/5-page scheduling by itself;
those remain required private-runner bindings, alongside the exact predeclared
SPY windows. No existing private source runner/binding was supplied or verified
in this task, so a replacement collector/credential path was not invented.

## Preflight stop and scientific boundaries

The attached context is the coding environment. Current supported managed
metadata showed **no configured acquisition secret/runtime-variable/outbound
identity bindings**. No credential values or files were inspected. It does not
establish an approved credential-separated acquisition context. Current observed
cgroup memory.max is8,589,934,592bytes (8GiB) and RLIMIT_AS is unlimited; the
required2GiB acquisition-job limit was not demonstrated. No4GiB private physical
quota/reserved free space or hard30-minute watchdog was verified. These are
concrete preflight failures; **no actual source requests were initiated**.

Owner's existing Alpaca use approval is recorded **OWNER_ATTESTED**, separately
from independently verified provider terms. No generic licensing/agreement
search, entitlement probe or new permission is invented or requested here.

The existing R-only-v1 policy is2025H1 screening, not an evidenced2025H2 extension
or proof of source-native share/round-lot conversion. Validator field names
`bid_size_round_lots`/`ask_size_round_lots` are not provider unit evidence. Native
size/condition/status/correction semantics stay unproved where the retained
sources do not establish them; no executable-source admission follows.

The unchanged pre-close source-quality windows are compatible with leaving the
post-close exit boundary unresolved **only as source-quality evidence**. No
overnight continuation, forced-flat position or substitute close fill is added.
Any executable exit/outcome claim still needs a separately specified resolution
boundary and reviewed source/status/size evidence before dependent evaluation.

Actual pilot status: **DATA_BLOCKED**,0new sessions,0new packets,0market HTTP
attempts,0retained market body bytes. Missing market record counts are unknown,
not zero. All12 planned packets remain NOT_RUN; Jan15's accepted restored sample
is reused as prior evidence, not re-downloaded or requalified. Any genuinely
covered Jan15 entry/delayed windows must be reused in the approved private runner.
The ordinary coding context did not import or inspect raw private market data.

## Executed engineering verification

Local Python3.12.14/Linux:15 focused enforcement tests PASS; full347-test suite
PASS, no failures/errors/skips; required300-bar demo PASS, generated performance
artifact unopened. Existing dependency environment reused; no installation.
The initial11 tests failed for the missing module. A later red regression
exposed insufficient settlement-reference validation during ledger replay; that
was fixed before the final15-test/full-suite pass. Earlier346-test evidence is
retained under its earlier binding; the changed replay guard justified the final
347-test run. No assertion was weakened.

An additional **offline enforcement check**, not a data pilot, executed two
separate Python processes over one fixture store: process1 consumed1 attempt/
2synthetic bytes; process2 reopened it, consumed attempt2/4cumulative bytes and
rejected a third request before its fake opener. Actual network calls0;
final existing-store verifier reported8valid records. This is direct executable
restart evidence for the accounting change, not market/source qualification.
Concurrent connections, pending failure, response-persistence interruption,
reconciliation, source pagination and error-body limits also passed focused tests.

Final full-suite wall12.2709s, child CPU11.9209user/0.5064system seconds,
peak child RSS119,276KiB. These describe tests, not acquisition performance.
External spend$0; included model/token/CI metering unavailable. Final independent
review and Ubuntu/Windows receipts belong in the draft PR; no merge authorized.

Critical path: approved private execution context with all remaining ceilings,
then reviewed enforcement binding before any data call. One author plus one fresh
independent reviewer; no other workers. Adopt existing source/storage components;
stop engine/restore/entitlement/framework repetition. Next3 within this work:
verify accounting, review/CI the isolated diff, checkpoint the unlaunched pilot.

NEXT_ACTION: Bind the reviewed accounting to an existing approved private source
context that demonstrates the sole ledger, packet/page limits,4GiB quota/reserve,
2GiB job memory and hard30-minute watchdog before the conditional pilot starts.

RESUME_PROMPT: Read this checkpoint, canonical policy/skill, current PRs and private
preflight manifest. Preserve0actual pilot calls, OWNER_ATTESTED use and unchanged
Jan15/Mar10/Jul3 windows and IQ-P1 protocol. Reuse accepted restoration/native
evidence. Do not initialize another actual ledger or repeat entitlement probes.
Execute only in the existing approved private credential-separated context after
all remaining hard ceilings/destinations are verified and this code's independent
review/CI are reconciled. Ordinary coding/review receives no credentials/private
raw data. Stop on any unknown gate; no source/exit admission or strategy inference.

## Local continuation

See [local offline qualification](LOCAL_QUALIFICATION_20261106.md) for the owner-directed Mac continuation, credential-test fix, Docker evidence and remaining launch blockers. Original science/accounting evidence above is retained.
