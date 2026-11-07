# IQ-P1 local Windows pilot — PR61

This is the fixed source-only acquisition path, not a strategy or experiment
registration. No Alpaca request is sent by Prepare, tests or CI. Real source
semantics/units/status/exit admission remain NOT_GRANTED. Earlier restoration,
LEAN and offline Docker qualifications are reused; they are not rerun here.

## Owner inputs (private; never paste keys or raw data into chat/GitHub)

- Windows 10/11 x64 with NTFS, UAC enabled, **all-users Python3.13 under
  Program Files**, all-users Git (`Program Files\Git\cmd`), and
  built-in diskpart/Storage PowerShell support. Use the same owner account for
  elevated approval and its linked standard-user acquisition token. Prepare
  proves the complete unelevated offline preflight; a different administrator
  account is unsuitable. Base Python/stdlib must be administrator-protected and
  its code hash is bound too. Per-user writable Python is rejected. If `py`
  selects another install, use `-PythonExe 'C:\Program Files\Python313\python.exe'`.
- A clean checkout at the **exact independently reviewed PR61 commit** with
  both Foundation OS jobs passing. Do not use a moving branch as approval.
- Existing approved retained January15 EvidenceStore directory (SQLite + objects).
  The original SQLite identity is pinned to PR56's already accepted
  `4ac083a8c23c2c24c4bd0d4bb08467f43d626d5dd959bab4b2e8561a9272f7c7`.
  Prepare selects the complete original quote chain covering both predeclared
  windows and pins its record/hash references. Nothing is redownloaded or
  represented as historical receipt. Missing/ambiguous originals stop setup.
- A reference to an **existing approved private acquisition credential file**,
  readable only by this owner/SYSTEM/Administrators. This launcher supports JSON
  with exactly `key_id` and `secret_key` fields. It does not discover .env files,
  create/copy credentials or call a broker SDK. Prepare checks only file/ACL
  metadata; contents are read only by the later standard-user acquisition job.
  If the owner's approved secret store is different, do not copy secrets into
  coding/CI or guess a binding: that concrete local binding needs owner setup.
- Confirm existing SIP entitlement/retention permission and zero incremental
  cost remain valid. The launcher cannot infer contract rights or account fees.

## One entry, two explicit stages

Open PowerShell **as Administrator under the same owner account**, in the repo.
Use the final reviewed forty-character commit from PR61, not the example token.

```powershell
.\tools\Start-IQP1Local.ps1 -Mode Prepare `
  -ReviewedCommit '<REVIEWED_40_CHARACTER_SHA>' `
  -ExistingCache 'C:\<existing-private-Jan15-store>' `
  -CredentialFile 'C:\<existing-private-acquisition-reference>.json'
```

Prepare creates one fixed4092MiB VHD in
`$env:LOCALAPPDATA\TradingAgent\IQP1`, mounts NTFS below `volume`, reserves64MiB
physically and installs the existing project requirements inside it (PyPI only,
no cache/environment credentials). Existing Python/Git/Windows are prerequisites,
not new pilot files. All new code/dependencies/evidence/SQLite/spool/temp/logs/
pilot backups stay in this VHD; bounded control files plus allocated VHD stay
below4GiB. This does not cap unrelated Windows/system/backup-service storage.

It authenticates the copied source/runtime, verifies private ACLs, fixed VHD
allocation and mounted identity, and probes the standard-user token using the
same protected named-job/query-only authentication and full offline preflight
that acquisition requires. It creates
one administrator-protected HKLM binding. It neither reads keys nor initializes
an HTTP allowance. Partial/failed setup is preserved; there is no format/reset
of existing media and no automatic second root.

Success prints `APPROVE_MANIFEST=<hash>`. Read the private `prepare.json` receipt
and confirm the three sessions, source-only scope, existing cache/credential
references and no new fees before authorizing. **Do not run Acquire during the
current no-Alpaca-request task.** Later explicit owner approval is this command:

```powershell
.\tools\Start-IQP1Local.ps1 -Mode Acquire `
  -ReviewedCommit '<SAME_REVIEWED_SHA>' `
  -CredentialFile 'C:\<same-existing-private-acquisition-reference>.json' `
  -ApproveManifest '<EXACT_HASH_PRINTED_BY_PREPARE>'
```

The elevated supervisor consumes a machine-protected one-shot authorization,
then starts the source worker with the owner's **unelevated UAC token**, suspended
until assigned to a kernel Job Object. The standard worker cannot reset that
latch or change the immutable code. Both bootstrap and credential-reading worker
authenticate membership in the exact administrator-owned kernel job recorded by
that claim. The standard token gets query rights only, preventing an alternate
job from impersonating this execution. Deleting/restoring a ledger cannot authorize
another allowance. Failure after consumption requires an explicit reviewed
reconciliation of the same usage, never deleting the latch or making a new ledger.

## Enforced boundary and private evidence

### Interrupted setup before source export

An earlier Prepare could leave only `pilot.vhd`, `volume\tmp` and the allocated
`volume\reserve.bin` after failing to export Git source. Source export is now
checked before creating a new VHD and reports `IQP1_PREPARE_SOURCE_EXPORT_FAILED`
without exposing arbitrary exception text.

For that exact early state only, the same launcher accepts `-Mode Prepare
-ResumePrepare` with the same Root/cache/credential-reference arguments and the
new reviewed commit. It inspects and reuses the existing attached fixed VHD and
reserve; it never formats, deletes, resets or makes another root. Prior diagnostic
records remain. Any machine registry key, manifest, receipt, source/runtime,
ledger or unexpected volume/tmp content blocks continuation. This is offline
setup recovery, not pilot resumption, and cannot be used with Acquire. All normal
quota/token/code/cache checks still apply before approval can be emitted.

- One global mutex/worker and one pinned evidence ID/path; fixed12 logical
  packets for Jan15, Mar10, Jul3 2025 SPY. Mandatory Jan15 quote reuse; only
  missing bars/windows can call the source. Bars1 page, quote windows5 pages.
- Existing durable128-attempt budget includes retry/error calls and settles only
  against stored response hashes. Retained cached HTTP bodies reduce the2e9-byte
  allowance before the first new request. Interrupted/pending work stays charged.
- GET only, HTTPS `data.alpaca.markets/v2/stocks/{bars,quotes}`, exact fixed query
  windows/symbol/feed, TLS validation, no proxy/redirect/calendar/order route.
  This is a reviewed transport allowlist, not a host-wide Windows firewall.
  No unreviewed executable receives credentials; trading flags remain false.
- Kernel aggregate/process commit limit is8MiB below2GiB, reserving headroom
  within the unchanged2GiB envelope. It is not a claim about total Windows RAM.
  This kernel limit covers the setup/acquisition child tree; the small watchdog
  Python process is separate from that job.
- Independent thirty-minute Job Object supervisor kills the whole tree, including
  hung calls/descendants; parent exit also kills it. Slow setup/source operations
  are inside that job. Suspend/wall-clock changes cannot replenish the deadline.
  Keep the machine awake; an OS cannot execute a kill while suspended.
- Fixed VHD allocation/identity and64MiB reserve+40MB free headroom are checked
  before source work. No extra collector, partitioning around page caps or order
  client is constructed. A limit/source/credential failure stops the pilot.

This boundary assumes a trusted owner and reviewed collector. It is not a general
Windows sandbox against hostile native programs running as the same user; those
can already read that user's credential file and may inject into processes.
Use a private account/runtime with no such processes. Administrator tampering or
external copies/backups are outside this collector's enforceable authority.

Private records are in `volume\evidence\evidence.sqlite` and `objects`; successful
summary is `volume\evidence\usage.json`. The ledger is authoritative even if the
summary is absent after a crash. Console prints only sanitized process resource
metrics and `STOP_REASON` codes. Bounded append-only `failure.jsonl` diagnostics
are in `volume\tmp` (or the control root before volume creation); they contain
no arbitrary exception text/keys/bodies and do not replace cumulative accounting.
Never publish raw response bodies/keys or the credential file. Keep the
VHD and ledger after stops; do not reset, rerun or inspect returns/holdouts.

After reboot an already created VHD may need administrator attachment. Preserve
it; use only `tools/iqp1_volume.ps1 -Action Attach -Root '<same root>'` before
inspection, never Initialize. Acquisition still requires the original untouched
one-shot authorization. An unsupported local token/ACL/volume condition fails
closed and is a concrete owner prerequisite, not permission to weaken a gate.
