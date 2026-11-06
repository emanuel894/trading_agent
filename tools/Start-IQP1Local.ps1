<# One entry. Prepare is offline with respect to Alpaca; Acquire needs explicit
   manifest-hash approval. No credential contents are arguments or environment. #>
param(
  [ValidateSet('Prepare','Acquire')][string]$Mode = 'Prepare',
  [string]$Root = "$env:LOCALAPPDATA\TradingAgent\IQP1",
  [Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{40}$')][string]$ReviewedCommit,
  [string]$ExistingCache = '',
  [string]$CredentialFile = '',
  [string]$ApproveManifest = '',
  [string]$PythonExe = ''
)
$ErrorActionPreference = 'Stop'
$repo = Split-Path $PSScriptRoot -Parent
# Git/source checks run inside the kernel deadline, before any private access.
$python = $PythonExe
if (-not $python) { $python = (& py -3.13 -I -c 'import sys; print(sys.executable)').Trim() }
if ($LASTEXITCODE -ne 0 -or -not (Test-Path -LiteralPath $python)) { throw 'IQP1_PYTHON_313_REQUIRED' }
$argsList = @('-I','-B',(Join-Path $PSScriptRoot 'iqp1_local.py'),$Mode,
  '--root',$Root,'--commit',$ReviewedCommit)
if ($ExistingCache) { $argsList += @('--cache',$ExistingCache) }
if ($CredentialFile) { $argsList += @('--credential-file',$CredentialFile) }
if ($ApproveManifest) { $argsList += @('--approve',$ApproveManifest) }
& $python @argsList
if ($LASTEXITCODE -ne 0) { throw "IQP1_STOPPED_EXIT_$LASTEXITCODE" }
