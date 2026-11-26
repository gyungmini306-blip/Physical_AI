$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$python = Join-Path $env:LOCALAPPDATA 'ESP32SchoolKit\python-env\Scripts\python.exe'
if (!(Test-Path -LiteralPath $python)) { throw 'Run common setup first.' }
& $python (Join-Path $PSScriptRoot 'native_db.py') start
exit $LASTEXITCODE
