param(
  [Parameter(Mandatory=$true)][ValidateSet('Stage','Inspect','Attach','Detach')][string]$Action,
  [Parameter(Mandatory=$true)][string]$Root,
  [string]$ExpectedVolumeGuid = ''
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

if ($Action -in @('Attach','Detach')) {
  if (-not (Test-Path -LiteralPath $image -PathType Leaf)) { throw 'IQP1_VOLUME_IMAGE_MISSING' }
  $current = Get-DiskImage -ImagePath $image -ErrorAction Stop
  if ($Action -eq 'Detach') {
    if (-not $current.Attached) { throw 'IQP1_VOLUME_ALREADY_DETACHED' }
    $null = Dismount-DiskImage -ImagePath $image -ErrorAction Stop
    if ((Get-DiskImage -ImagePath $image -ErrorAction Stop).Attached) {
      throw 'IQP1_VOLUME_DETACH_NOT_CONFIRMED'
    }
    @{detached=$true} | ConvertTo-Json -Compress
    exit 0
  }
  if ($current.Attached) { throw 'IQP1_VOLUME_ALREADY_ATTACHED' }
  $null = Mount-DiskImage -ImagePath $image -NoDriveLetter -ErrorAction Stop
  if (-not (Get-DiskImage -ImagePath $image -ErrorAction Stop).Attached) {
    throw 'IQP1_VOLUME_ATTACH_NOT_CONFIRMED'
  }
  @{attached=$true} | ConvertTo-Json -Compress
  exit 0
}

# Inspect is read-only. It verifies the identity of the mounted VHD created by
# the supervised Python worker and never attaches/formats physical storage.
if (-not (Test-Path -LiteralPath $image -PathType Leaf)) { throw 'IQP1_VOLUME_IMAGE_MISSING' }
$diskImage = Get-DiskImage -ImagePath $image -ErrorAction Stop
if (-not $diskImage.Attached) { throw 'IQP1_VOLUME_DETACHED_OWNER_MUST_ATTACH' }
$disk = $diskImage | Get-Disk -ErrorAction Stop
# The owner worker resolves the folder mount point through the Win32 mount
# manager to a GUID path. Verify that GUID against this VHD's own volume;
# textual 8.3 vs long directory aliases cannot bypass or spuriously fail it.
if ($ExpectedVolumeGuid -notmatch '^\\\\\?\\Volume\{[0-9A-Fa-f-]{36}\}\\$') {
  throw 'IQP1_MOUNT_IDENTITY_MISMATCH'
}
$parts = @($disk | Get-Partition -ErrorAction Stop)
if ($parts.Count -ne 1) { throw 'IQP1_MOUNT_IDENTITY_MISMATCH' }
$volume = $parts[0] | Get-Volume -ErrorAction Stop
if ($volume.UniqueId -ne $ExpectedVolumeGuid -or $parts[0].DiskNumber -ne $disk.Number) {
  throw 'IQP1_MOUNT_IDENTITY_MISMATCH'
}
if ($volume.FileSystem -ne 'NTFS' -or $volume.FileSystemLabel -ne 'IQP1' -or $volume.HealthStatus -ne 'Healthy') {
  throw 'IQP1_VOLUME_NOT_HEALTHY_NTFS'
}
@{volume_id=$volume.UniqueId; free_bytes=[long]$volume.SizeRemaining;
  size_bytes=[long]$volume.Size; image_bytes=[long]$diskImage.Size;
  disk_number=$disk.Number; mount=$mount; filesystem=$volume.FileSystem} | ConvertTo-Json -Compress
