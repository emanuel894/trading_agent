# Independent Q04 timing adjudication

Fresh read-only `issue21_adjudication` reviewer examined trusted base
67317e573624529e247d98a4964f946421b571e7 and the preserved c70aa32 packet.
Requested route gpt-6-astra/high; served model/reasoning support unobservable.
Independent context, no cross-provider claim. No writes or native runs.

Ruling: **authored fixture timing error**, not an intentional prior-session
ingress requirement. Matrix Q04 requires missing/overlapping mappings to reject
before order at the Jan7 boundary; shared q1 is decision-relative +1s. The author
explicitly relocates ordinary boundary variants' events, while malformed variants
override decision but inherit the Jan6 default event. Their decision quotes are
already Jan7 I2 quotes; moving the decision back would invalidate that scenario.

Permit only four scalar changes: in Q04_missing and Q04_overlap, events[0].event_ns
and available_ns move from 1736175601000000000 (Jan6 15:00:01Z) to
1736260201000000000 (Jan7 14:30:01Z), exactly decision+1s. Preserve all expected
bytes and every other input field. Keep q1's I1 identity: it is expired/ineligible,
including exactly the extended interval end in overlap, and cannot rescue entry.
No clock backdating, dispatch tolerance, ticker substitution or economic change.

Adjudication authorizes only the v3 proposal. A different fresh reviewer must
review the actual amended bytes before any native execution.
