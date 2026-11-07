param(
  [Parameter(Mandatory=$true)][ValidateSet('Stage','Inspect')][string]$Action,
  [Parameter(Mandatory=$true)][string]$Root
)
$ErrorActionPreference = 'Stop'
# Only bounded reviewed diagnostic tokens may leave this privileged helper.
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

if ($Action -eq 'Stage') {
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
  @{staged=$true} | ConvertTo-Json -Compress
  exit 0
}

# Inspect is read-only. It verifies the identity of the mounted VHD created by
# the supervised Python worker and never attaches/formats physical storage.
if (-not (Test-Path -LiteralPath $image -PathType Leaf)) { throw 'IQP1_VOLUME_IMAGE_MISSING' }
$diskImage = Get-DiskImage -ImagePath $image -ErrorAction Stop
if (-not $diskImage.Attached) { throw 'IQP1_VOLUME_DETACHED_OWNER_MUST_ATTACH' }
$disk = $diskImage | Get-Disk -ErrorAction Stop
# Resolve the actual volume at the folder mount, not the textual AccessPaths.
# Windows can canonicalize the same folder as an 8.3 path, so string equality
# would reject a correctly mounted VHD or accept an unverified alias.
$volumes = @(Get-Volume -Path $mount -ErrorAction Stop)
if ($volumes.Count -ne 1) { throw 'IQP1_MOUNT_IDENTITY_MISMATCH' }
$volume = $volumes[0]
$parts = @(Get-Partition -Volume $volume -ErrorAction Stop)
if ($parts.Count -ne 1 -or $parts[0].DiskNumber -ne $disk.Number) {
  throw 'IQP1_MOUNT_IDENTITY_MISMATCH'
}
if ($volume.FileSystem -ne 'NTFS' -or $volume.FileSystemLabel -ne 'IQP1' -or $volume.HealthStatus -ne 'Healthy') {
  throw 'IQP1_VOLUME_NOT_HEALTHY_NTFS'
}
@{volume_id=$volume.UniqueId; free_bytes=[long]$volume.SizeRemaining;
  size_bytes=[long]$volume.Size; image_bytes=[long]$diskImage.Size;
  disk_number=$disk.Number; mount=$mount; filesystem=$volume.FileSystem} | ConvertTo-Json -Compress
