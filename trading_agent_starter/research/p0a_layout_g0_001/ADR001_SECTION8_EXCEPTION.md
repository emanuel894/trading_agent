# Proposed synthetic inert-layout exception — review copy 1.0.0

**PROPOSED / UNAPPLIED / INACTIVE.** No scientific registration is modified.

Target: `trading_agent_starter/ARCHITECTURE_DECISION_001.md`, SHA256
`8e550b45447c616138704715f2de4424c392bacc0d4b7939aa077a72657b3641`.
Insertion point: immediately after §8's existing Untrusted documents paragraph,
ending “BUY/SELL schema, model escalation or conversational trading agents are
added now.” Preserve that paragraph and every scientific gate byte-for-byte.
The exact candidate diff is ADR001_SECTION8.proposed.patch, retained as data;
do not run `git apply` on it under this task.

The insertion reuses the proposed exception in accepted PR50 at
f812f2afb5b94fd3be2f40f1bd38454c72cfda47, OWNER_DECISION.md §2, and makes its
execution prerequisites explicit through the hash-bound PR50 contract and final
runtime/fixture manifests. It is limited to synthetic qualification; neither
security review acceptance nor G0 preparation authorizes the gate.

Normative constraints retain original-byte provenance, visible/hidden/ambiguous
accounting, typed iXBRL checks, materiality/completeness controls and whole-document
ambiguity rejection. Exact PR50 gate limits/families/oracles/no-repair conditions
are incorporated by immutable reference, not copied into a new mutable gate.
The existing narrowly qualified passive SEC annotation diagnostic allowance is
unchanged; arbitrary unsupported CSS/warnings remain fatal. No renderer can
supply its own independent reference oracle.

The primary component pin is the existing WeasyPrint70.0 revision
7e2dda0d7833916d2698c35e707bc80ddea1ed24. Full runtime/native/container/font/
license/enforcement and fixture/oracle manifests must be independently reviewed
and accepted **before** separate owner gate authorization and any layout invocation.
Missing runtime pins or G0 evidence are not excused by textual amendment acceptance.

G0 is currently BLOCKED on exact font identity/availability/license evidence.
The trusted ADR remains unchanged and the proposed exception inactive. No authentic
input, inference, SEC request, spending, broker action or unrelated PR merge can
be authorized through this paragraph. Original scientific single-repair stopping
rule remains separate and untouched. The final review receipt must distinguish
text acceptance from deployment-security/G0 acceptance and gate authorization.
