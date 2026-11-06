param([Parameter(Mandatory=$true)][string]$File, [Parameter(Mandatory=$true)][string]$OwnerSid)
$ErrorActionPreference = 'Stop'
$acl = Get-Acl -LiteralPath $File
$allowed = @($OwnerSid, 'S-1-5-18', 'S-1-5-32-544')
foreach ($entry in $acl.Access) {
  if ($entry.AccessControlType -eq 'Allow' -and
      $allowed -notcontains $entry.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value) {
    throw 'IQP1_CREDENTIAL_FILE_NOT_PRIVATE'
  }
}
if ($allowed -notcontains $acl.Owner -and
    $allowed -notcontains ([Security.Principal.NTAccount]$acl.Owner).Translate([Security.Principal.SecurityIdentifier]).Value) {
  throw 'IQP1_CREDENTIAL_FILE_OWNER_INVALID'
}
