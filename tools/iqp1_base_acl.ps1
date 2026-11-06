param([Parameter(Mandatory=$true)][string]$Base)
$ErrorActionPreference = 'Stop'
Import-Module "$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1" -Force
$trusted = @('S-1-5-18','S-1-5-32-544',
  'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
$items = @((Get-Item -LiteralPath $Base -Force)) + @(Get-ChildItem -LiteralPath $Base -Recurse -Force |
  Where-Object { $_.FullName -notmatch '\\site-packages(\\|$)' })
$writeRights = [Security.AccessControl.FileSystemRights]'Write,Delete,DeleteSubdirectoriesAndFiles,ChangePermissions,TakeOwnership'
foreach ($item in $items) {
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'IQP1_BASE_RUNTIME_LINK_REJECTED' }
  $acl = Get-Acl -LiteralPath $item.FullName
  if ($trusted -notcontains $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value) {
    throw 'IQP1_BASE_PYTHON_NOT_PROTECTED'
  }
  foreach ($entry in $acl.Access) {
    # Read-only app-container ACEs can be unresolvable by account name on
    # localized Windows. They cannot modify the protected Python runtime.
    if ($entry.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) { continue }
    if ($entry.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow) { continue }
    if (-not ($entry.FileSystemRights -band $writeRights)) { continue }
    # Unresolvable identities with write rights remain a hard failure.
    try {
      $sid = $entry.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    } catch [System.Security.Principal.IdentityNotMappedException] {
      throw 'IQP1_BASE_PYTHON_UNMAPPED_WRITABLE_ACCOUNT'
    }
    if ($trusted -notcontains $sid) {
      throw 'IQP1_BASE_PYTHON_IS_WRITABLE'
    }
  }
}
