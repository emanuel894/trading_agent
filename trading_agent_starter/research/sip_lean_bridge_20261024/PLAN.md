# Offline SIP → pinned LEAN observation bridge

Owner mandate: implement the minimum deterministic offline integration using the
verified private SIP archive; no further rights searches. Rights stay unresolved.
No source collection, strategy/returns, scientific edits or trading.

1. Open the existing SQLite store read-only; reuse EvidenceStore chain/blob verifier
   without its write-initializing constructor. Bind original DB hash; no missing
   directory/database initialization. Reuse existing SIP bar/quote validators.
2. Require exact SIP/raw/1Min/asof=- window and complete source page-token chains.
   Preserve source record/hash/row lineage and nanoseconds. Deduplicate identical
   observations; fail ambiguous conflicting same-time rows. Exclude incomplete
   endpoint bars. Unknown historical receipt, status and size-unit qualification
   stay unknown; never infer them from quotes or retrieval clocks.
3. Convert to pinned LEAN TradeBar/Tick public types in a tiny observation-only
   codec. Preserve original ns separately; native timestamps round upward to100ns.
   Diagnostic symbol is not a verified instrument identity. No QCAlgorithm,
   portfolio, signals, order methods or fill engine; full strategy mapping remains
   a separately authorized follow-up, not claimed by this transport test.
4. Test adversarial synthetic stores, run authentic private projection twice and
   native roundtrip twice with network disabled. Preserve payload/output privately,
   publish hashes/counts only. Full suite/demo, independent review, exact-head CI.
5. Commit meaningful checkpoints and stop at technical observation compatibility
   plus explicit source/science boundaries. Reuse PR28/51; no qualification reruns.
