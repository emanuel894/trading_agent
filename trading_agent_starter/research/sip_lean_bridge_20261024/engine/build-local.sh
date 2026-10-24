#!/bin/sh
# Use new writable container-local staging; readonly accepted /runtime mount.
set -eu
mkdir app
for ref in /usr/share/dotnet/packs/Microsoft.NETCore.App.Ref/*/ref/net10.0/*.dll /runtime/*.dll; do
    printf '%s\n' "-r:$ref" >> refs.rsp
done
dotnet /usr/share/dotnet/sdk/10.0.402/Roslyn/bincore/csc.dll -nologo -noconfig -nostdlib -deterministic -target:exe -main:SipEngine.Entry -out:app/SipEngine.dll @refs.rsp EngineReplay.cs
cp /runtime/*.dll app/
printf '%s\n' '{"runtimeOptions":{"tfm":"net10.0","framework":{"name":"Microsoft.NETCore.App","version":"10.0.13"}}}' > app/SipEngine.runtimeconfig.json
