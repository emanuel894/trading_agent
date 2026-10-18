# Issue 17 terminal-runtime packet

Scope: Q01–Q03 only, synthetic data, isolated C# LEAN host. This does not qualify
Q04–Q33, research integration, actual data, broker plugins, trading, alpha or
production security. The authoritative design and immediate stop rules remain
[Issue17](https://github.com/emanuel894/trading_agent/issues/17) and
[the merged design](../../LEAN_CONTRACT_QUALIFICATION_20261018.md).

Read `checkpoint.json`, `PROGRESS.md` and the final decision/report before resuming.
Do not repeat completed source/dependency work or successful pairs bound to the
same frozen input and host hash. No scheduling tool or known quota reset time was
exposed in this client; no resume or heartbeat was invented/scheduled.

## Evidence and boundaries

- `fixtures/`: original pre-execution oracle/input bytes. Failed attempts are not
  relabeled PASS. Original input preparation revisions precede any fixture run.
- `fixtures_v2/`: independently reviewed source-grounded callback-order correction
  plus stronger time/identity/native-order/phase/reservation/NAV assertions.
  [ORACLE_REVISION.md](ORACLE_REVISION.md) explains the exact limited change.
- `host/`: ordinary LEAN AlgorithmManager, SubscriptionSynchronizer,
  DataManager/UniverseSelection and BacktestingTransactionHandler; public setup
  and brokerage-notification override. Fixture feed only replaces ingress;
  transaction/portfolio/removal/cleanup and native end callback are not mocked.
  Result sampling/publication is disabled; no performance metrics are accepted.
- `compare.py`: independent exact fixture comparator; no equity-curve tolerance,
  event sorting or alternative-order acceptance.
- `run_gate.py`: bounded cloud-workspace runner; validates runtime/input hashes,
  starts fresh network-none processes, preserves controls/logs, stops on first
  divergence, reuses only verified successful pairs on the same host hash and
  removes its disposable container after preserving observations.
- `build/manifest.json`, `build/locks/`: exact source/tree, SDK/container digest,
  runtime, 13 resolved project locks, 28 package versions/normalized content
  hashes and raw package hashes, and 125 runtime file hashes. Public-source
  tracked files remain unchanged. No official broker plugin is installed.
- `attempts/`: immutable unqualified preparation attempts and source/build
  snapshots. `evidence/`: raw/canonical runtime results and container controls.
  Logs have diagnostic wall clocks; canonical JSON excludes those clocks.

NuGet normalized content hashes and raw signed-package SHA512 are distinct;
metadata/locks and raw `.nupkg.sha512` were checked separately. Default TLS and
NuGet verification were preserved. `dotnet nuget verify --all` on the initially
questioned Accord package confirmed the normalized content hash/signature.
Source-pinned packages report DotNetZip1.16.0 high and System.Drawing.Common4.7.0
critical audit warnings. Logs are preserved; versions/checks were not patched or
suppressed. This isolated trusted-fixture run does not admit the stack for
production or processing untrusted financial documents.

## Reproduction on the selected cloud workspace

Research Python 3.13 stays in its existing isolated environment. LEAN source,
packages and built host live separately under `/workspace/issue-17-lean`, outside
the repository. Retained runtime/source hashes must match before reuse. A cold
NuGet cache archive may exist under `/tmp/issue17-spill`; its hash/location are in
the checkpoint. Do not infer that ephemeral caches survive another environment.

For a clean recreation, fetch **only** LEAN commit
`d4cac37514427c84d40064cecbf3f0e6be4b0137` into the separate `source/` directory;
copy `host/` next to it, and copy each recorded lock back to the matching project
path. Obtain the official SDK image by the recorded immutable digest, not its
moving `10.0` tag. Use ordinary public package/source access only for restore:

```sh
dotnet restore host/LeanTerminal.csproj --locked-mode -p:RestorePackagesWithLockFile=true
dotnet build host/LeanTerminal.csproj --no-restore -c Release -p:RunAnalyzers=false
```

These commands run in the pinned SDK container with `NUGET_PACKAGES=/work/packages`.
The initial managed build passed inherited HTTP/HTTPS proxy bindings by name and
mounted public CA certificates read-only, copied them into the disposable build
container and ran `update-ca-certificates`; no credential or TLS bypass was used.
Do not pass a whole host environment or mount a Docker socket into the fixture.
Record newly built binary hashes separately; a different binary is not silently
substituted for the observed run.

Place the frozen `fixtures_v2/` next to the built host and run explicit cases via
`run_gate.py`. Its current paths intentionally name this qualification workspace;
adapt directory locations explicitly on another machine, preserving the hashes.
Each fixture uses the pinned image, `--network none --read-only --cap-drop ALL`,
`no-new-privileges`, unprivileged UID65534, a limited tmpfs, read-only source/runtime/
fixtures and a separate output mount. It receives only disabled trading flags,
not broker/data/model credentials. It verifies loopback-only interfaces and a
TEST-NET connection returning NetworkUnreachable. Container settings are retained.

Compare each canonical JSON to its frozen independent oracle, then require two
byte-identical full JSON SHA256 values from separate processes. Input IDs/hash,
identity, ordered event times, native order states/fees, cash, positions, unresolved
claims, cancellation reservations and entry-denial probes are exact assertions.
Full frozen-input replay here is fresh process re-execution, not a native memory
checkpoint. Q27 crash-cut qualification remains unrun/out of scope.

The existing Python suite/demo and hosted Ubuntu/Windows Foundation checks remain
mandatory and distinct from Linux-only LEAN runtime qualification. No new CI
workflow, project dependency, policy, registration or activation setting is added.
