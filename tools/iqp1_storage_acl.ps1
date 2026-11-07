param([ValidateSet('Harden','Verify')][string]$Action,
      [Parameter(Mandatory=$true)][string]$Root, [Parameter(Mandatory=$true)][string]$OwnerSid)
$ErrorActionPreference = 'Stop'
Import-Module "$env:SystemRoot\System32\WindowsPowerShell\v1.0\Modules\Microsoft.PowerShell.Security\Microsoft.PowerShell.Security.psd1" -Force
$rootPath = [IO.Path]::GetFullPath($Root).TrimEnd('\')
$admin = [Security.Principal.SecurityIdentifier]'S-1-5-32-544'
$system = [Security.Principal.SecurityIdentifier]'S-1-5-18'
$owner = [Security.Principal.SecurityIdentifier]$OwnerSid
# Enumerate managed content without ever descending into the volume's protected
# OS metadata. Filtering after -Recurse is too late (and would alter its ACL).
$volumePath = Join-Path $rootPath 'volume'
$items = New-Object 'System.Collections.Generic.List[object]'
$items.Add((Get-Item -LiteralPath $rootPath -Force))
foreach ($entry in (Get-ChildItem -LiteralPath $rootPath -Force | Where-Object Name -ne 'volume')) {
  $items.Add($entry)
}
$volumeItem = Get-Item -LiteralPath $volumePath -Force
$items.Add($volumeItem)
$pending = New-Object 'System.Collections.Generic.Stack[object]'
$pending.Push($volumeItem)
while ($pending.Count) {
  $parent = $pending.Pop()
  foreach ($entry in (Get-ChildItem -LiteralPath $parent.FullName -Force)) {
    if ($parent.FullName.TrimEnd('\') -eq $volumePath -and
        $entry.Name -ceq 'System Volume Information' -and
        ([int]$entry.Attributes -band 0x16) -eq 0x16 -and
        -not ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint)) { continue }
    if ($entry.Attributes -band [IO.FileAttributes]::ReparsePoint) { throw 'IQP1_UNEXPECTED_REPARSE_POINT' }
    $items.Add($entry)
    if ($entry.Attributes -band [IO.FileAttributes]::Directory) { $pending.Push($entry) }
  }
}
foreach ($item in $items) {
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and
      $item.FullName.TrimEnd('\') -ne (Join-Path $rootPath 'volume')) { throw 'IQP1_UNEXPECTED_REPARSE_POINT' }
  $mutable = $item.FullName -match ('^' + [regex]::Escape((Join-Path $rootPath 'volume')) + '\\(evidence|tmp)(\\|$)')
  if ($Action -eq 'Harden') {
    if ($item.Attributes -band [IO.FileAttributes]::Directory) {
      $security = New-Object Security.AccessControl.DirectorySecurity
      $inherit = [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit'
    } else {
      $security = New-Object Security.AccessControl.FileSecurity
      $inherit = [Security.AccessControl.InheritanceFlags]::None
    }
    $security.SetOwner($admin)
    $security.SetAccessRuleProtection($true,$false)
    foreach ($sid in @($admin,$system,$owner)) {
      $rights = if ($sid -eq $owner -and -not $mutable) {'ReadAndExecute'} else {'FullControl'}
      $rule = New-Object Security.AccessControl.FileSystemAccessRule($sid,$rights,$inherit,'None','Allow')
      $security.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $item.FullName -AclObject $security
  }
  $acl = Get-Acl -LiteralPath $item.FullName
  $actualOwner = $acl.GetOwner([Security.Principal.SecurityIdentifier]).Value
  if ((-not $mutable -and ($actualOwner -ne $admin.Value -or -not $acl.AreAccessRulesProtected)) -or
      ($mutable -and @($admin.Value,$system.Value,$owner.Value) -notcontains $actualOwner)) {
    throw 'IQP1_STORAGE_ACL_OWNER_OR_INHERITANCE_INVALID'
  }
  foreach ($rule in $acl.Access) {
    $sid = $rule.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($rule.AccessControlType -ne 'Allow' -or @($admin.Value,$system.Value,$owner.Value) -notcontains $sid) {
      throw 'IQP1_STORAGE_ACL_NOT_PRIVATE'
    }
    if ($sid -eq $owner.Value -and -not $mutable -and
        ($rule.FileSystemRights -band [Security.AccessControl.FileSystemRights]'Write,Delete,ChangePermissions,TakeOwnership')) {
      throw 'IQP1_IMMUTABLE_RUNTIME_IS_WRITABLE'
    }
  }
}
