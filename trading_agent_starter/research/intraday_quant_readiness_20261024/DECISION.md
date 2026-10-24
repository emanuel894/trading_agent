# DATA_BLOCKED — first historical intraday Quant readiness

2026-10-24. **Proposal only; no registration or experiment activated.**
Trusted active integration base: `feat/alpaca-paper-foundation`
@`5f8b850548e2f7786814086d5350a72a19d87459`. Live REST branch/ref,
merged PR51 and Git fetch agree. Main is not the integration base.
Post-merge Foundation runs40022965881/40022958273 report success at that SHA.
Canonical policy/skill/state map read; the map's old LEAN status is superseded
by PR28/PR51, not a reason to repeat qualification. Evidence bindings are in
`evidence.json`; all references below are existing base-commit artifacts.

## What exists, and what it admits

| Existing evidence/component | Proven scope | Remaining limit for this proposal |
| --- | --- | --- |
| PR28 accepted LEAN gate; PR51 recovered executor and integration | Qualified synthetic public engine/accounting boundary, Linux containers; eight new deterministic integration runs; preserved cost/isolation receipts | Not real-feed mapping, full-day/year replay, source admission or production latency. Reuse unchanged; no native reruns here. |
| `research/sip_quote_review_20260916.json` | Supplied historical AAPL/SPY SIP window2025-01-15T15:00–15:05Z; six1Min bars each;60,895 quote rows across seven HTTP records. Source chain9 records VERIFIED; database SHA4ac083a8…; HTTP access accepted | Repeated requests may duplicate observations. Not a population sample, complete session, year coverage or current entitlement guarantee. Raw archive not found in this checkout's runs; retained summary is evidence, not recreated raw bytes. |
| Same quote review |60,438 row-timestamp screen passes;435 locked+22 crossed; no malformed/zero-size rows; B/C tapes, R condition | Row timestamp pass is NOT actionability. Zero status rows. Tape A not empirically sampled. Do not extrapolate99.25% to a year. |
| `research/historical_quote_policy_v1.json`; final `dated_source_gate_20260916.json` | Later freeze supersedes earlier review's policy_frozen=false. Historical-R-only-v1: positive bid<ask, conditions exactly[R], tapes A/B/C, both exchange codes, positive sizes, age≤2s, spread≤20bp; acquisition-screening review PASS | Frozen for2025H1 historical acquisition screening, not permission to extend scope to2025H2 or certify fills/depth. Independent field/tape/version mapping and scope approval required; no new threshold fitting. |
| `owner_daily_smoke_attestation_20260922.json` | Owner attests3 SIP1Day rows per AAPL/SPY, no gaps/duplicates/rejected rows, verified local store | Raw archive and exact date range not supplied here; not independently replayed. Daily buckets are not1Min RTH bars. No60-session/year coverage inferred. |
| `agent/audit_market.py:SIPSource.pages`, EvidenceStore | Existing explicit feed=sip/asof=-/sort=asc/1Min/raw bars and quote pagination,50-page cap, original bytes/provenance; native-ns validator | Quote endpoint has no adjustment parameter. `asof=-` prevents implicit ticker mapping; it is NOT a revision-vintage selector. Existing context method is tied to10-Q opportunities; do not use its scheduling as this study's contract. |
| `MARKET_DATA_CONTRACT.md`, `agent/alpaca_history.py` | Tested30Min IEX/raw completion/session/gap contract;60s assumed publication lag; bounded SDK pagination | IEX is hard-required in that adapter. This is not a SIP dataset or measured60s availability. Do not silently repurpose the CLI/feed or recompute Amendment003 liquidity. |
| `source_rights_20260916.json:alpaca_sip` | Public terms/schema snapshots pinned; successful historical access; no purchase shown necessary | ACCESS_PASS_RIGHTS_UNRESOLVED: actual applicable subscriber/account/exchange terms for automated/non-display personal research, immutable storage, derived analysis and retention absent. No blanket prohibition or permission invented. Raw licensed data stays private. |
| `cohort_spy_identity_20260916.json` | SPY trust units/CIK0000884394, internal lineage, NYSE Arca anchors in two retained filings;1993 commencement is operations, not listing date | intervals_complete=false; not continuous2025 class/ticker/listing/action proof. No modern asset-list substitution or full security master needed. |
| Existing calendar/action/halt packets | Calendar references include Jan9 national mourning, DST/early-close rules; finite historical RSS responses and source references | No complete SPY2025 halt/suspension/carry-in/resumption or corporate-action/distribution coverage. A quote or empty halt search cannot establish tradability. RSS retention rights unresolved. |
| `config/access_gate_observations.json` | Historical SIP success retained separately from realtime NOT_ENTITLED; status subscription NOT_TESTED_AUTH_BLOCKED | No fresh authenticated calls here. Realtime denial alone does not block a historical study; a live subscription would not repair historical rights/status/receipt gaps. |

No real-data input bundle is presently admitted to the proposed experiment.
Software contracts, finite source observations and historical access evidence
are reusable; source-specific permission and coverage remain separate gates.
No new official retrieval is useful yet: public marketing cannot supply the
owner's accepted agreement or missing private archive. No Alpaca/SEC requests,
credential/environment loading, source contact or performance inspection occurred.

## Exact decision-changing missing items

1. **Rights:** applicable accepted agreement/version plus scoped review of local
   automated research, immutable audit retention and derived outputs. No keys,
   account IDs or private legal text in Git/CI. Publish only sanitized finding/hash.
2. **Private raw evidence and coverage:** restore original complete SIP store;
   verify chain/objects against retained provenance. For later2025 study, separately
   obtain a frozen per-session1Min bar/quote manifest with complete pagination,
   request bounds, raw hashes, duplicate/conflict/gap counts and collection vintage.
   Existing five-minute evidence must not be re-probed merely because absent here.
3. **SPY boundary:** dated2025 unit/ticker/venue lineage and action/distribution
   intervals, split/share-unit treatment and explicit halt/suspension carry-in,
   resumption and coverage/correction limitations. Known sessions alone insufficient.
4. **Temporal/execution qualification:** source event times versus original receipt
   and revision clocks; quote tape/conditions/size units and round-lot conversion
   valid for each date; ambiguity ordering/corrections; raw RTH minute semantics.
   Historical receipt stays null. No fabricated arrival clock or adjusted fill.
5. **Owner science decision:** approve a NEW separate proposal below, its conditional
   retrospective estimand/assumed delay and dates/risks/costs before acquiring study
   outcomes or evaluating returns. Then qualify only the real-data manifest→existing
   LEAN mapping. No generic platform or new engine qualification is on this path.

Unknown historical receipt is irrecoverable from a later REST response. For an
explicitly approved exploratory corrected-vintage study it is a declared model
limitation, not something to invent or repair with a live subscription. It
prevents claims of actual historical decision availability/live executable alpha.
If the owner requires such a PIT claim, absent original vintages/receipts BLOCK
that stronger study; use a separately authorized prospective design instead.

## Smallest executable next step and stop

**One offline evidence handoff:** owner supplies the original private SIP archive
and applicable agreement to the approved private research location; no credentials.
On a writer-closed copy run the existing
`python -m agent.evidence_audit --store <private-copy> verify` from
`trading_agent_starter`, compare database/raw hashes and produce a sanitized rights
finding. Do not repeat quote-quality research already completed. Stop if objects,
chain/bindings or permissions are unresolved. This is not a request to download
new prices, run a strategy, expand a vendor search or provide keys to coding/CI.

Ranked next3: (1) this offline rights/archive reconciliation; (2) only after owner
approval, a capped SPY source-only qualification of calendar/status/actions and
three predeclared sessions (Jan15 ordinary, Mar10 DST, Jul3 early-close), reusing
Jan15 evidence and inspecting zero strategy outcomes; (3) after qualification,
freeze full2025 manifests and approve registration before a separately mandated
one-shot replay. New acquisition caps must be justified from the private sample's
unique page/body sizes; no broad download or arbitrary cap is authorized here.

ADOPT existing SIPSource/EvidenceStore/qualified LEAN. KEEP only necessary source
admission/mapping. No new collector, security master, ML or broker infrastructure.
One focused owner plus independent final reviewer; no parallel supplier audit.
External spending **$0**; paid automation disabled; included usage only, monetary
resource/model-token accounting unavailable. Existing scientific and frozen files
remain byte-identical. Stop at DATA_BLOCKED; no automatic implementation/merge.
