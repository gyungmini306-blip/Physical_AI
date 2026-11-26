$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
function New-Password {
    $bytes = New-Object byte[] 24
    $rng = [System.Security.Cryptography.RandomNumberGenerator]::Create()
    try { $rng.GetBytes($bytes) } finally { $rng.Dispose() }
    return ([BitConverter]::ToString($bytes)).Replace('-', '').ToLowerInvariant()
}
try {
    if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
        throw 'Docker Desktop is required for this setup.'
    }
    & docker info --format '{{.OSType}}'
    if ($LASTEXITCODE -ne 0) { throw 'Start Docker Desktop first.' }
    & docker compose version
    if ($LASTEXITCODE -ne 0) { throw 'Docker Compose v2 is required.' }
    if (-not (Test-Path -LiteralPath '.env')) {
        $rootPassword = New-Password
        $appPassword = New-Password
        [System.IO.File]::WriteAllLines((Join-Path $PSScriptRoot '.env'), [string[]]@(
            "MARIADB_ROOT_PASSWORD=$rootPassword",
            "MARIADB_PASSWORD=$appPassword"
        ), [System.Text.Encoding]::ASCII)
        Write-Host 'Created local .env. Keep it private and back it up.'
    }
    & docker compose up -d --wait --wait-timeout 240
    if ($LASTEXITCODE -ne 0) { throw 'MariaDB startup failed. Run docker compose logs db.' }
    & docker compose ps
    if ($LASTEXITCODE -ne 0) { throw 'Cannot check container status.' }
    Write-Host 'MariaDB ready on 127.0.0.1:3307.'
    Write-Host 'Database: temperature_alert; user: temperature_app.'
    Write-Host 'Password: MARIADB_PASSWORD in local .env.'
    exit 0
} catch {
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}
