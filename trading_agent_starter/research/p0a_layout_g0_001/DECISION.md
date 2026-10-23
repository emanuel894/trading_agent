# G0 pre-execution decision 1.0.0

**BLOCKED — G0 is not qualified. No synthetic gate authorization is requested.**
P0A_INCOMPLETE. Current owner authority covers amendment preparation/independent
security review and G0 checks only. It does not authorize layout, the32-family
gate, authentic processing, research inference, spending or scientific changes.

## First disqualifying prerequisite

**G0_FONT_IDENTITY_AND_LICENSE_UNQUALIFIED.** PR50 pins WeasyPrint source but
explicitly leaves the native/runtime/font/image lock unresolved. Its accepted
logical font families are Times New Roman, Arial Narrow, Calibri and Segoe UI
Symbol; no exact font files, face/style coverage, hashes, licensed artifact source
or approved physical-font aliases were supplied. The local Fontconfig inventory
returned583 records and **zero exact-family matches for all four**. It also
reported no writable cache directory; this host inventory is a bounded availability
observation, not a qualified font configuration or proof of global unavailability.

Under the current explicit no-font-substitution instruction, choosing a fallback,
alias or different font would cross owner authority. Neither a package name,
matching family label, installed system font nor a remote download alone establishes
the exact file's license/rights and reproducible source. No substitute was chosen;
no font was downloaded, scanned for metrics or used for layout. Missing hashes
and rights evidence remain missing rather than inferred from an engine license.

Runtime preparation stopped at this prerequisite. The table below is the complete
G0 disposition **at the required first-blocker stop**, not a completed runtime lock.

| G0 requirement | Verified observation / disposition |
| --- | --- |
| Exact candidate | PR50 live-confirmed draft/unmerged at f812f2afb5b94fd3be2f40f1bd38454c72cfda47; retained70.0 source pin7e2dda0d7833916d2698c35e707bc80ddea1ed24 unchanged. No substitute engine. |
| Exact font files/config/aliases and rights | **BLOCKED** as above. No executable font lock or license clearance exists. |
| Exact CPython | Host `/usr/bin/python3.13` is **3.13.5**, SHA256889c603f0d17cb54060951bcf4c4f9b8c9ebd9e52b392c70209bbb9755d797d9; it is not the proposed3.13.16 and was not substituted. This hash is host evidence, not the candidate runtime lock. |
| Container image availability | Managed local daemon queried read-only: Docker28.4.0; no cached images. Exact base/candidate image digest NOT_RESOLVED. No pulls/builds/runs. No claim that the exact image is globally unavailable. |
| Native/direct/transitive artifacts and licenses | NOT_QUALIFIED / STOPPED_BEFORE_RESOLUTION. Existing source version ranges and license declarations do not establish exact artifacts, full SBOM, native ABI or redistribution rights. No artifact/license hashes invented. |
| OS isolation | Docker reports seccomp builtin, cgroup namespace, cgroupv2/cgroupfs. These are capabilities, **not enforcement qualification**. Worker memory/CPU/PID/network/filesystem/syscall enforcement NOT_TESTED. No weakened host-process alternative. |
| Supervisor/adapter/UA/locale/oracle manifest | NOT_IMPLEMENTED / NOT_FROZEN. PR50's frozen16 positive/16 adversarial families and resource/no-repair rules remain unchanged. No fixtures run. |
| Immutable source and science | Imported evidence untouched; protected ADR/registrations/parser unchanged. No original SEC object processed. |

## Diagnostic interpretation and privilege boundary

Default-sandbox local Docker access failed with socket EPERM. A narrowly scoped
socket filesystem grant failed in sandbox setup (a mount-target error), not an
automatic approval rejection. A subsequently approved **read-only** local-socket
daemon query succeeded; no daemon start/restart or permission/configuration change
was made. User namespace setup inside the coding sandbox failed opening uid_map
as read-only; `/sys/fs/cgroup` is not writable there. These observations must not
be exaggerated into “the managed daemon is unavailable” or “container isolation
is impossible.” The actual proposed worker's enforcement remains unqualified.

No privileged container, host networking, mount relaxation, alternate runtime,
font fallback, Docker restart, credential inspection or security weakening was
used. The daemon's presence does not qualify resource/isolation limits by itself.
Harmless G0 capability queries are separate from PR50's frozen synthetic cases;
they consume no layout/replay/repair attempt and supply no gate-pass evidence.

## Amendment and next executable action

ADR001_SECTION8.proposed.patch contains the **exact unapplied insertion**, anchored
to the protected ADR's current SHA256. ADR001_SECTION8_EXCEPTION.md identifies
the target, authority and unchanged guards. Independent security review may accept
the proposed text, but cannot accept an absent deployment lock or activate it.
The original “never render” rule remains in force. No amendment or registration
is applied/merged, even if textual review is accepted while G0 remains blocked.

**Next executable action:** supply the exact intended font files, complete face/
glyph coverage and lawful artifact/license evidence for the accepted families,
with explicit owner approval of their physical identity. Do not silently approve
different aliases. Then resume only the remaining G0 lock/containment checks in
the same bounded candidate path. If the intended files cannot be lawfully made
available at$0, stop this route; a different font/contract needs a separate owner
decision, not an implementation substitution.

Only after independently reviewed amendment text **and** the full exact G0 artifact/
license/enforcement manifest are accepted may explicit authorization for the
single frozen synthetic gate be sought. No authorization request for that gate is
appropriate now. Current direction is not inferred consent to run it later.

Scientific50-filing single parser/access repair gate (ADR001§8 line277) is unchanged
and separate from engineering accounting. PR47 used one engineering repair;
V2's second authentic implementation/replay remains unspent. No counters reset,
no new authentic attempt granted, no custom CSS/layout development or architecture
study restarted. Coverage1/12, authentic MD&A0/1, real inferenceNOT_MEASURED,
G4 clock/source/representation conflictsUNRESOLVED. External spend$0.
