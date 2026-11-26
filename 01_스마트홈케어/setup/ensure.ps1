# Windows 10/11 x64. Installs native tools without Docker.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$root = Join-Path $env:LOCALAPPDATA 'ESP32SchoolKit'
$cache = Join-Path $root 'downloads'
$apps = Join-Path $root 'apps'
$venv = Join-Path $root 'python-env'
$failures = New-Object System.Collections.Generic.List[string]
New-Item -ItemType Directory -Force -Path $root,$cache,$apps | Out-Null
function Step([string]$name,[scriptblock]$action) {
    Write-Host "=== $name ===" -ForegroundColor Cyan
    try { & $action } catch { $failures.Add($name); Write-Warning $_.Exception.Message }
}
function Find-Python {
    $candidates = @()
    if (Get-Command py -ErrorAction SilentlyContinue) {
        $found = & py -3 -c "import sys; print(sys.executable) if sys.version_info >= (3,10) else exit(1)" 2>$null
        if ($LASTEXITCODE -eq 0) { $candidates += $found }
    }
    $candidates += (Join-Path $env:LOCALAPPDATA 'Programs\Python\Python312\python.exe')
    if (Get-Command python -ErrorAction SilentlyContinue) {
        $candidate = (Get-Command python).Source
        if ($candidate -notlike '*\WindowsApps\*') { $candidates += $candidate }
    }
    foreach($candidate in $candidates) {
        if ($candidate -and (Test-Path -LiteralPath $candidate)) {
            & $candidate -c "import sys,venv; assert sys.version_info >= (3,10)" 2>$null
            if ($LASTEXITCODE -eq 0) { return $candidate }
        }
    }
    return $null
}
Step 'Arduino IDE / CLI / ESP32 / CP210x' {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'arduino.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Arduino setup failed; see its install.log.' }
}
Step 'Python / USB / BLE dashboard' {
    $vp = Join-Path $venv 'Scripts\python.exe'
    $ready = $false
    if (Test-Path -LiteralPath $vp) {
        & $vp -c "import sys; assert sys.version_info >= (3,10); import serial,bleak,tkinter" 2>$null
        $ready = ($LASTEXITCODE -eq 0)
    }
    if ($ready) { Write-Host 'Python dependencies already installed.'; return }
    $python = Find-Python
    if (!$python) {
        if (!(Get-Command winget -ErrorAction SilentlyContinue)) { throw 'Python 3.10+ and WinGet unavailable. Install Python from python.org and run setup again.' }
        & winget install --id Python.Python.3.12 --exact --scope user --accept-package-agreements --accept-source-agreements --disable-interactivity
        $python = Find-Python
        if (!$python) { throw 'Python not detected after WinGet. Reopen setup or install Python 3.10+ manually.' }
    }
    $vp = Join-Path $venv 'Scripts\python.exe'
    if (!(Test-Path -LiteralPath $vp)) {
        & $python -m venv $venv
        if ($LASTEXITCODE -ne 0) { throw 'Python environment creation failed.' }
    }
    & $vp -m pip install -r (Join-Path $PSScriptRoot '..\esp32-dual-connection\pc\requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    & $vp -c "import serial,bleak,tkinter; print('Python dependencies OK')"
    if ($LASTEXITCODE -ne 0) { throw 'Python import check failed.' }
}
if ($failures.Count) {
    Write-Host ('FAILED: ' + ($failures -join ', ')) -ForegroundColor Red
    exit 1
}
Write-Host 'Assignment environment ready.' -ForegroundColor Green
exit 0
