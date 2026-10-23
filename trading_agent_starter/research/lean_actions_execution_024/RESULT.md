# Q12–Q20 staged qualification

Foundation: `ba213d8d775c20db7a299932a9ea3319c9bc8a59`, verified against live
`feat/alpaca-paper-foundation`; PR #20 is merged. This dedicated branch adds only
this fixture packet. Q01–Q11 are not rerun; Q21–Q33 remain unqualified and unrun.
The final gate state, independent review, exact final head, local checks and both
Foundation CI job URLs are published on the draft PR after final-head validation.
`NATIVE_RESULT.json` records the exact staged native evidence and binding hashes.

| Requirement | Accepted evidence |
| --- | --- |
| Q12 integral | Reused Issue23 Q11_integral_coupling attempts132/133, original bindings in reuse-proof.json. Native20@50, pending4@50, reservation200+fee1, no split profit/cash. |
| Q12 reverse | v1 attempts1/2: whole1@200 plus unresolved0.5 claim; no cached-price cash; documented37 paid once. |
| Q13 payable | v1 attempts3–6: native dividend20 encumbered until evidence, spendable9000, raw98 and NAV10000; missing payable remains nonspendable. |
| Q14 merger | v1 attempts7–12: documented5 I2 plus70 receivable/payment; missing/conflict unresolved. Tax allocation remains null; native aggregate book cost1000 carried separately from economic value970. v2 duplicate-delivery case closes the global once-only invariant. |
| Q15 rename | v1 attempts13–18: stable SID/holding/order/intent, mapping once; old ticker quote rejected; date-only/overlap unresolved. v2 duplicate delivery leaves mapping/version and business outputs unchanged. |
| Q16 halts | v1 attempts19–28: fresh resumed quote entry, no-resume/unknown/no-fresh no entry, original deadline cancellation, separate scheduled sell waits through halt and extended-hours decoy. |
| Q17 slippage | Reused original Q06_age_exact attempts25/26 for isolated5bps buy100.07001 under original bindings. v1 attempts29–32 prove sell99.95 and stress buy100.12002; v2 proves stress sell99.9 (=99.90), fee1 each, native stock slippage0. |
| Q18 capacity | v2 shared event capacity5: first3 fills, frozen second3 rejected with2 remaining, repeated scans cannot replenish; independent quote permits separately authorized3. |
| Q19 race | v2 canonical and same-availability reordered/duplicate execution batches: nativeheld6, cash9398.57994, fee1, reservations600.42006→400.28004→0 only after cancel evidence. |
| Q20 fees | v2 verified0/1/1.25, no-fill0, missing/unbounded rejection, incremental1/0/.2 partial fees; evidenced post-cancel correction−.1 once to total1.1, no extra fill. |

## Immutable stages and preserved failure

The original v1 fixtures, host, build and all33 attempts stay byte-identical,
checked by continuation_v2/parent-preserved.json. Its32 accepted processes form16
exact deterministic pairs under their original bindings. They do not claim to
have run against the continuation binary.

Attempt33 stopped at `$.fills[0].price: '99.9' != '99.90'`. Its failed verdict,
output hash `25eee7ab4345473af3a27be42aead2ece7e181595f188c6d160715bd0dcca872`
and original oracle are retained. Independent adjudication established a single
authored representation error: existing `Program.Num` uses G29 canonical decimal
format; the frozen fill-price literal was not canonicalized. The versioned v2
oracle changes that one string to99.9, exactly the same decimal value. The exact
comparator and all economic inputs stay unchanged. Attempt33 is never relabeled.

V2 retains all27 original case objects and26 original expected records unchanged;
it adds merger/rename duplicate cases and exactly two `Once` guards before action
mutation. The two new expected business files are byte-identical to the original
known merger/exact rename files. Only13 corrected, unrun or new cases execute
against v2, each twice; no previously accepted process is repeated. New v2 outputs
retain their own input/fixture/build/code hashes and append-only launch journal.

## Engine limitations and boundaries

This is public-API adapter qualification against pinned LEAN
`d4cac37514427c84d40064cecbf3f0e6be4b0137`, not an unmodified-defaults or production
readiness claim. Native fractional split fallback credits cached-price cash;
reverse actions are intercepted before that path and explicit whole holdings are
projected. Native dividend credit requires an external encumbrance. Native symbol
change handling cancels tickets, so exact external mapping updates stable SID.
Native execution callbacks need adapter idempotence and monotone logical status.
Q19 uses a public fake brokerage emission seam and delayed cancel acknowledgement;
it does not establish native automatic partial fills or actual plugin behavior.
Admission probes exercise isolated callback guards before submission; Q15 variants
select frozen mapping evidence. These establish fixture guard outcomes, not a
general resolver or integration into a production order API. Fee corrections use
public fee/holding APIs with explicit evidence. No private API,
reflection, durable LEAN core patch or fabricated economics is used.

The synthetic fee fragmentation convention requires review before production
partial-fill evaluation. Real action economics, venue rounding, broker/provider
entitlements and Q21–Q33 need their own authorized qualification; this packet
activates no Paper/Live capability and establishes no alpha.

## Efficiency and validation lineage

Two focused source passes and the frozen source hashes establish relevant public
semantics before runtime. Reuse avoids both accepted integral-split and5bps-buy
pairs, every Q01–Q11 runtime, and16 accepted v1 pairs after the scoped continuation.
The original27 runtime variants cover only behavior not already established;
two added duplicate cases close a concrete review finding. No broad framework
audit, unrelated data acquisition, paid calls or purchases occurred.

Oracle approval precedes native execution in each stage. The final review is a
fresh independent Codex context, not a cross-provider qualification. Final-head
local validation includes the full repository suite, prior/stage comparators,
terminal regression, amendment/continuation preservation and demo. Logs and exact
head are published in the PR without changing the validated commit. Foundation
CI independently runs Python3.13 tests and demo on Ubuntu and Windows; it does not
claim a Windows LEAN execution.
