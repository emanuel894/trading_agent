param(
  [Parameter(Mandatory=$true)][ValidateSet('Initialize','Inspect','Attach','Detach')][string]$Action,
  [Parameter(Mandatory=$true)][string]$Root,
  [ValidateRange(64,4092)][int]$SizeMiB = 4092
)
$ErrorActionPreference = 'Stop'
$Root = [IO.Path]::GetFullPath($Root).TrimEnd('\')
if ($Root -notmatch '^[A-Za-z]:\\' -or $Root.Contains('"') -or $Root.Contains("`n") -or $Root.Contains("`r")) {
  throw 'IQP1_UNSAFE_VOLUME_PATH'
}
$image = Join-Path $Root 'pilot.vhd'
$mount = (Join-Path $Root 'volume') + '\'
function Invoke-Diskpart([string[]]$Commands) {
  $script = Join-Path $Root '_diskpart.txt'
  try {
    [IO.File]::WriteAllLines($script, $Commands, [Text.Encoding]::ASCII)
    $null = & "$env:SystemRoot\System32\diskpart.exe" /s $script
    if ($LASTEXITCODE -ne 0) { throw 'IQP1_DISKPART_FAILED' }
  } finally { Remove-Item -LiteralPath $script -Force -ErrorAction SilentlyContinue }
}
if ($Action -eq 'Initialize') {
  if (Test-Path -LiteralPath $image) { throw 'IQP1_EXISTING_VOLUME_PRESERVE_NO_RESET' }
  $null = New-Item -ItemType Directory -Path $Root -Force
  if (Get-ChildItem -LiteralPath $Root -Force) { throw 'IQP1_INITIALIZE_REQUIRES_EMPTY_ROOT' }
  $null = New-Item -ItemType Directory -Path $mount
  Invoke-Diskpart @("create vdisk file=`"$image`" maximum=$SizeMiB type=fixed",
    "select vdisk file=`"$image`"", 'attach vdisk', 'create partition primary',
    'format fs=ntfs quick label=IQP1', "assign mount=`"$mount`"")
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
