# Isolated continuation build

Reuse `/workspace/issue-19-lean` read-only; do not build into its host/runtime.
Copy this packet's `host/` and `fixtures/` to `/workspace/issue-23-lean`.
The project references the original runtime's public assemblies directly; it has
no new NuGet package dependency or source patch. Exclude original host assemblies
from references to avoid duplicate public host-class definitions.

Build with the original manifest's immutable SDK image:

```sh
docker --host=unix:///var/run/docker.sock run --rm --network none \
  --volume /workspace/issue-19-lean:/work:ro \
  --volume /workspace/issue-23-lean:/continuation \
  --workdir /continuation/host \
  --env DOTNET_CLI_HOME=/tmp/dotnet \
  --env DOTNET_CLI_TELEMETRY_OPTOUT=1 \
  mcr.microsoft.com/dotnet/sdk@sha256:0d99ebf1ccad15037b5c98c9fe8979d6b8dbac23812feae2277a0b277b5c5ffa \
  dotnet build LeanGap.csproj --configuration Release --ignore-failed-sources
```

Then `python build_manifest.py` checks shared output files byte-for-byte against
old runtime hashes and freezes all new runtime/code hashes. Its absolute workspace
paths describe this qualification host, not product configuration. Native launches
require independent approval bound to this manifest and the input/oracle/code.

Build01 succeeded with duplicate host-type warnings; preserved log. Build02
excluded those old host references and had zero warnings/errors. Build03 added
clock-preserving factor probes. Build04 passes the actual Raw enumerator Tick to
SetMarketPrice; both builds had zero warnings/errors. No native fixture executed
under any superseded build. Build01 specified NuGetAudit=false on a project with
no package references; subsequent builds omitted that unnecessary property.
Original source-pinned dependency audit evidence remains untouched.

The native Raw enumerator deliberately never calls the factor provider. A
quarantined Adjusted probe proves factor consumption via its public path. That
probe is not execution: normalization metadata rejects it before SetMarketPrice.
Its daily factor-row date never substitutes for the envelope's intraday clocks.
Each admitted factor revision gets a fresh diagnostic enumerator because native
refresh is daily. No earlier process, raw mark, trade, input or manifest is edited.
