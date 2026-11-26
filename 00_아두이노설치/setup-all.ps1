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
Step '1/4 Arduino IDE / CLI / ESP32 / CP210x' {
    & powershell.exe -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot 'setup.ps1')
    if ($LASTEXITCODE -ne 0) { throw 'Arduino setup failed; see its install.log.' }
}
Step '2/4 DHT sensor libraries' {
    $cli = Join-Path $apps 'arduino-cli\arduino-cli.exe'
    if (!(Test-Path -LiteralPath $cli)) { throw 'Arduino CLI missing.' }
    & $cli lib update-index
    if ($LASTEXITCODE -ne 0) { throw 'Library index update failed.' }
    & $cli lib install 'DHT sensor library' 'Adafruit Unified Sensor'
    if ($LASTEXITCODE -ne 0) { throw 'DHT library setup failed.' }
}
Step '3/4 Python / Flask / pyserial / PyMySQL' {
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
    & $vp -m pip install -r (Join-Path $PSScriptRoot 'requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Python dependency installation failed.' }
    & $vp -c "import flask,serial,pymysql,sqlite3; print('Python dependencies OK')"
    if ($LASTEXITCODE -ne 0) { throw 'Python import check failed.' }
}
Step '4/4 MariaDB Windows ZIP (no Docker)' {
    $version = '11.4.14'
    $name = "mariadb-$version-winx64"
    $dest = Join-Path $apps $name
    $bin = Join-Path $dest 'bin'
    $server = Join-Path $bin 'mariadbd.exe'
    if (!(Test-Path -LiteralPath $server)) {
        $zip = Join-Path $cache "$name.zip"
        $url = "https://archive.mariadb.org/mariadb-$version/winx64-packages/$name.zip"
        if (!(Test-Path -LiteralPath $zip)) {
            try {
                Invoke-WebRequest -Uri $url -OutFile "$zip.part" -UseBasicParsing
                Move-Item -LiteralPath "$zip.part" -Destination $zip -Force
            } catch { Remove-Item -LiteralPath "$zip.part" -Force -ErrorAction SilentlyContinue; throw }
        }
        Expand-Archive -LiteralPath $zip -DestinationPath $apps -Force
    }
    if (!(Test-Path -LiteralPath $server)) { throw 'MariaDB executable missing. Check download/extraction.' }
    & $server --no-defaults --version
    if ($LASTEXITCODE -ne 0) { throw 'MariaDB failed to run. Check Windows x64 and Microsoft Visual C++ runtime.' }
    Write-Host "MariaDB binary ready: $server"
}
if ($failures.Count) {
    Write-Host ('FAILED: ' + ($failures -join ', ')) -ForegroundColor Red
    exit 1
}
Write-Host 'Common setup completed. Run the assignment MariaDB setup next.' -ForegroundColor Green
exit 0
