param([ValidateSet('Harden','Verify')][string]$Action,
      [Parameter(Mandatory=$true)][string]$Root, [Parameter(Mandatory=$true)][string]$OwnerSid)
$ErrorActionPreference = 'Stop'
$rootPath = [IO.Path]::GetFullPath($Root).TrimEnd('\')
$admin = [Security.Principal.SecurityIdentifier]'S-1-5-32-544'
$system = [Security.Principal.SecurityIdentifier]'S-1-5-18'
$owner = [Security.Principal.SecurityIdentifier]$OwnerSid
# Never follow an unexpected junction/symlink while replacing ACLs.
$items = @((Get-Item -LiteralPath $rootPath -Force)) + @(Get-ChildItem -LiteralPath $rootPath -Force |
  Where-Object Name -ne 'volume') + @((Get-Item -LiteralPath (Join-Path $rootPath 'volume') -Force)) +
  @(Get-ChildItem -LiteralPath (Join-Path $rootPath 'volume') -Recurse -Force)
foreach ($item in $items) {
  if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -and
      $item.FullName.TrimEnd('\') -ne (Join-Path $rootPath 'volume')) { throw 'IQP1_UNEXPECTED_REPARSE_POINT' }
  $mutable = $item.FullName -match ('^' + [regex]::Escape((Join-Path $rootPath 'volume')) + '\\(evidence|tmp)(\\|$)')
  if ($Action -eq 'Harden') {
    if ($item.PSIsContainer) {
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
