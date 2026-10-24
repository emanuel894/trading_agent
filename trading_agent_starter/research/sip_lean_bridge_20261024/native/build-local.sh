#!/bin/sh
# Run in a new container-local writable staging directory with public sources only.
# /runtime is the accepted runtime read-only mount; image/assembly pins in RESULT.
set -eu
mkdir app
for ref in /usr/share/dotnet/packs/Microsoft.NETCore.App.Ref/*/ref/net10.0/*.dll /runtime/QuantConnect.Common.dll /runtime/Newtonsoft.Json.dll /runtime/NodaTime.dll; do
    printf '%s\n' "-r:$ref" >> refs.rsp
done
dotnet /usr/share/dotnet/sdk/10.0.402/Roslyn/bincore/csc.dll -nologo -noconfig -nostdlib -deterministic -target:exe -out:app/SipObservation.dll @refs.rsp Program.cs
cp /runtime/*.dll app/
printf '%s\n' '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.13"}}}' > app/SipObservation.runtimeconfig.json
