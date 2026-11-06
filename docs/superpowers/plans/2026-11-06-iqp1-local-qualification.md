# Local IQ-P1 continuation (owner-directed inline execution)

Base d3fa9e19610f73fc6f92d64b6784091e3f515dfd, local/iqp1-pilot.
Owner asked for direct execution, no terminal relay, no Alpaca request/merge/spend.

1. Reproduce credential-test dotenv discovery with a sentinel blocking file discovery
   and socket connection. Patch only credential fixture setup; preserve runtime behavior.
2. Export committed source without local secret/runtime paths. Build a digest-pinned
   Python image. Qualify offline only: nonroot, read-only root, network none, 2GiB
   memory/no swap, bounded shared scratch/reserve and <=1800s worker watchdog.
3. Run full suite/demo and physical boundary probes; independent scoped review.
4. Save exact results and remaining acquisition gates. Keep PR draft, never claim
   scratch-only validation supplies persistent private acquisition or a complete
   4GiB host-wide disk quota. No broker calls, orders, merge or credential access.

Reuse existing EvidenceStore, ReadOnlyHTTP and IQP1HTTPBudget. Do not add a collector
or initialize a real pilot ledger. Existing request/body accounting tests validate
128/2e9 ceilings offline; they do not authorize unbudgeted egress or a new store.

Review focus: .env discovery before fixtures, source-only context, detached worker
termination, every writable scratch/backup/reserve path, and distinguishing worker
watchdog from unqualified host/daemon/startup/cleanup duration.
