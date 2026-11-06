param([Parameter(Mandatory=$true)][string]$Base)
$ErrorActionPreference = 'Stop'
Import-Module "$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1" -Force
$trusted = @('S-1-5-18','S-1-5-32-544',
  'S-1-5-80-956008885-3418522649-1831038044-1853292631-2271478464')
$items = @((Get-Item -LiteralPath $Base -Force)) + @(Get-ChildItem -LiteralPath $Base -Recurse -Force |
  Where-Object { $_.FullName -notmatch '\\site-packages(\\|$)' })
foreach ($item in $items) {
  if ($item.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'IQP1_BASE_RUNTIME_LINK_REJECTED' }
  $acl = Get-Acl -LiteralPath $item.FullName
  if ($trusted -notcontains $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value) {
    throw 'IQP1_BASE_PYTHON_NOT_PROTECTED'
  }
  foreach ($entry in $acl.Access) {
    if ($entry.PropagationFlags -band [Security.AccessControl.PropagationFlags]::InheritOnly) { continue }
    $sid = $entry.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($entry.AccessControlType -eq 'Allow' -and $trusted -notcontains $sid -and
        ($entry.FileSystemRights -band [Security.AccessControl.FileSystemRights]'Write,Delete,DeleteSubdirectoriesAndFiles,ChangePermissions,TakeOwnership')) {
      throw 'IQP1_BASE_PYTHON_IS_WRITABLE'
    }
  }
}
