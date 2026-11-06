param(
  [Parameter(Mandatory=$true)][ValidateSet('Initialize','Inspect','Attach','Detach')][string]$Action,
  [Parameter(Mandatory=$true)][string]$Root,
  [ValidateRange(64,4092)][int]$SizeMiB = 4092
)
$ErrorActionPreference = 'Stop'
# Forward only structured bounded diagnostics; never reveal raw diskpart text.
trap {
  $message = [string]$_.Exception.Message
  if ($message -match '^(IQP1_[A-Z0-9_]{1,100})$') {
    [Console]::Error.WriteLine('IQP1_SAFE_FAILURE_CODE=' + $Matches[1])
  } else {
    [Console]::Error.WriteLine('IQP1_SAFE_FAILURE_CODE=IQP1_VOLUME_UNCLASSIFIED_ERROR')
  }
  exit 1
}
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
if ($Root -notmatch '^[A-Za-z]:\\' -or $Root.Contains('"') -or $Root.Contains("`n") -or $Root.Contains("`r")) {
  throw 'IQP1_UNSAFE_VOLUME_PATH'
}
$image = Join-Path $Root 'pilot.vhd'
$mount = (Join-Path $Root 'volume') + '\'
function Get-InitializeFailurePhase {
  # Read-only inspections of the named VHD; never select/format a physical disk.
  if (-not (Test-Path -LiteralPath $image -PathType Leaf)) { return 'CREATE' }
  try {
    $diskImage = Get-DiskImage -ImagePath $image -ErrorAction Stop
    if (-not $diskImage.Attached) { return 'ATTACH' }
    $disk = $diskImage | Get-Disk -ErrorAction Stop
    $parts = @($disk | Get-Partition -ErrorAction Stop)
    if ($parts.Count -eq 0) { return 'PARTITION' }
    $mounted = @($parts | Where-Object { $_.AccessPaths -contains $mount })
    if ($mounted.Count -ne 1) {
      $formatted = @($parts | Get-Volume -ErrorAction SilentlyContinue |
        Where-Object { $_.FileSystem -eq 'NTFS' -and $_.FileSystemLabel -eq 'IQP1' })
      if ($formatted.Count -eq 0) { return 'FORMAT' }
      return 'ASSIGN'
    }
    return 'VERIFY'
  } catch { return 'VHD_INSPECT' }
}
function Invoke-Diskpart([string[]]$Commands) {
  $script = Join-Path $Root '_diskpart.txt'
  try {
    [IO.File]::WriteAllLines($script, $Commands, [Text.Encoding]::ASCII)
    # Capture native output but do not expose host paths or arbitrary text.
    $nativeOutput = @(& "$env:SystemRoot\System32\diskpart.exe" /s $script 2>&1)
    $exitCode = $LASTEXITCODE
    $reportedError = [bool](($nativeOutput -join "`n") -match '(?i)DiskPart has encountered an error|Virtual Disk Service error|DiskPart failed')
    if ($exitCode -ne 0 -or $reportedError) {
      $phase = if ($Action -eq 'Initialize') { Get-InitializeFailurePhase } else { $Action.ToUpperInvariant() }
      throw "IQP1_DISKPART_${phase}_FAILED"
    }
  } finally { Remove-Item -LiteralPath $script -Force -ErrorAction SilentlyContinue }
}
if ($Action -eq 'Initialize') {
  if (Test-Path -LiteralPath $image) { throw 'IQP1_EXISTING_VOLUME_PRESERVE_NO_RESET' }
  $null = New-Item -ItemType Directory -Path $Root -Force
  $existing = @(Get-ChildItem -LiteralPath $Root -Force)
  foreach ($entry in $existing) {
    if ($entry.Name -ne 'failure.jsonl' -or $entry.PSIsContainer -or $entry.Length -gt 65536 -or
        ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { throw 'IQP1_INITIALIZE_REQUIRES_EMPTY_ROOT' }
    foreach ($line in [IO.File]::ReadAllLines($entry.FullName)) {
      $record = $line | ConvertFrom-Json
      if ($record.reason -notmatch '^[A-Z][A-Z0-9_]{0,120}$' -or
          $record.mode -notin @('prepare-child','seed','verify-child','acquire-bootstrap','acquire-child') -or
          $null -eq $record.at_unix) { throw 'IQP1_INVALID_BOUNDED_FAILURE_DIAGNOSTIC' }
    }
  }
  $null = New-Item -ItemType Directory -Path $mount
  Invoke-Diskpart @("create vdisk file=`"$image`" maximum=$SizeMiB type=fixed",
    "select vdisk file=`"$image`"", 'attach vdisk', 'create partition primary',
    'format fs=ntfs quick label=IQP1', "assign mount=`"$mount`"")
  if (-not (Test-Path -LiteralPath $image -PathType Leaf)) {
    throw 'IQP1_DISKPART_CREATE_FILE_MISSING'
  }
}
if ($Action -eq 'Detach') {
  Invoke-Diskpart @("select vdisk file=`"$image`"", 'detach vdisk')
  exit 0
}
if ($Action -eq 'Attach') {
  Invoke-Diskpart @("select vdisk file=`"$image`"", 'attach vdisk')
}
$diskImage = Get-DiskImage -ImagePath $image
if (-not $diskImage.Attached) {
  if ($Action -eq 'Inspect') { throw 'IQP1_VOLUME_DETACHED_OWNER_MUST_ATTACH' }
}
$disk = $diskImage | Get-Disk
$parts = @($disk | Get-Partition | Where-Object { $_.AccessPaths -contains $mount })
if ($parts.Count -ne 1) { throw 'IQP1_MOUNT_IDENTITY_MISMATCH' }
$volume = $parts[0] | Get-Volume
if ($volume.FileSystem -ne 'NTFS' -or $volume.FileSystemLabel -ne 'IQP1' -or $volume.HealthStatus -ne 'Healthy') {
  throw 'IQP1_VOLUME_NOT_HEALTHY_NTFS'
}
@{volume_id=$volume.UniqueId; free_bytes=[long]$volume.SizeRemaining;
  size_bytes=[long]$volume.Size; image_bytes=[long]$diskImage.Size;
  disk_number=$disk.Number; mount=$mount; filesystem=$volume.FileSystem} | ConvertTo-Json -Compress
