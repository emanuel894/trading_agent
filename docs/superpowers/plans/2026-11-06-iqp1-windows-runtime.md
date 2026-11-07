# IQ-P1 Windows local runtime plan

Owner instruction: continue PR61, complete Windows engineering/tests, prepare one
local launch process; no Alpaca requests, secrets, purchases or merge now.
Starting live head:1dca2c0e077b5db9d839483e43195af71105ebc2. Existing offline Docker
qualification and353-test CI are reused; they do not qualify persistent Windows
storage or host-wide timing. Only Linux execution/GitHub tools are accessible.

Implement a fixed-purpose Windows path, reusing source_packet, EvidenceStore,
ReadOnlyHTTP, SIPSource.pages and IQP1HTTPBudget. No replacement collector/engine.

1. Add a strict Alpaca Data GET opener/frozen12-window plan, read-only cache
   access and source-only pilot join. January15 entry/delay evidence must be
   reused before any new request. Unknown units/status/revisions remain unknown.
2. Add a Windows-native Job Object supervisor (suspended child assigned before
   execution; aggregate memory cap; process-tree termination on absolute wall
   deadline; no unbounded cleanup after timeout).
3. Add fixed VHD/NTFS storage setup and inspection using built-in Windows tools.
   Bound the entire managed pilot root to4GiB: fixed4092MiB VHD plus bounded
   control metadata; evidence/source/venv/temp/spool/backups/logs live inside.
   Verify fixed footer, allocation/size, mount identity, reserve and quota before
   source use. Never reformat existing/unknown media; preserve evidence on stop.
4. Anchor the sole root/volume/owner in an administrator-created Windows binding;
   normal acquisition cannot change it. One OS mutex/worker; durable HTTP and
   per-packet states survive restarts. Acquisition deadline never resets.
5. One PowerShell entry defaults to Prepare/offline. Export committed source
   only; no .env/key copying. Explicit later owner approval of the prepared
   manifest is required for Acquire; credentials are read only in that local
   private job, never during Prepare, tests, CI or by coding/review agents.
6. Test route denials, cache reuse, packet/byte bounds and failure recovery;
   Windows CI additionally exercises actual Job Object memory/tree timeout and
   temporary VHD persistence/ENOSPC. Reuse accepted qualification receipts.
7. Fresh independent review, final-head required CI, update PR61 only. Deliver
   exact owner Prepare and later approval commands, with honest local-machine
   verification limits. No acquisition during this task.

Storage scope is all files created/retained by this pilot, including copied code,
dependencies and control files; it is not a bound on Windows, existing Python,
system logs, unrelated backups or the whole machine. Administrative setup is
one-time; real collection runs without elevation. Unsupported OS/privileges or
unverified quota/memory/deadline/credentials/cache/route binding must fail closed.
