# Windows 10/11 x64, PowerShell 5.1+. Official vendor packages only.
# Installs user-space IDE/CLI/core; CP210x driver may request administrator approval.
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$Root = Join-Path $env:LOCALAPPDATA 'ESP32SchoolKit'
$Cache = Join-Path $Root 'downloads'
$Apps = Join-Path $Root 'apps'
$IdeDir = Join-Path $Apps 'arduino-ide'
$CliDir = Join-Path $Apps 'arduino-cli'
$DriverDir = Join-Path $Apps 'cp210x'
$Cli = Join-Path $CliDir 'arduino-cli.exe'
$Sketch = Join-Path $ScriptDir 'sketches\SmartHomeCare'
$BoardUrl = 'https://espressif.github.io/arduino-esp32/package_esp32_index.json'
$IdeZip = Join-Path $Cache 'arduino-ide_2.3.10_Windows_64bit.zip'
$CliZip = Join-Path $Cache 'arduino-cli_1.5.1_Windows_64bit.zip'
$DriverZip = Join-Path $Cache 'CP210x_Universal_Windows_Driver.zip'
$IdeUrl = 'https://github.com/arduino/arduino-ide/releases/download/2.3.10/arduino-ide_2.3.10_Windows_64bit.zip'
$CliUrl = 'https://github.com/arduino/arduino-cli/releases/download/v1.5.1/arduino-cli_1.5.1_Windows_64bit.zip'
$DriverUrl = 'https://www.silabs.com/documents/public/software/CP210x_Universal_Windows_Driver.zip'
$IdeSha256 = '5dd9d6b2e2c9ef8dd9d98da7808f712daff97911a91d3ccfaf946355c6b6abb3'
$CliSha256 = 'fabe42e0eb04d00e776a66178299ff95a46c623dbc260f997e58fd514853dd40'

function Say([string]$Text) { Write-Host "[ESP32] $Text" -ForegroundColor Cyan }
function Fetch([string]$Url, [string]$Path, [string]$Hash='') {
  if (Test-Path -LiteralPath $Path) {
    if (!$Hash -or (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash -ieq $Hash) {
      Say "Cache: $(Split-Path $Path -Leaf)"
      return
    }
    Remove-Item -LiteralPath $Path -Force
  }
  for ($tryNo=1; $tryNo -le 3; $tryNo++) {
    $part = "$Path.part"
    try {
      Remove-Item -LiteralPath $part -Force -ErrorAction SilentlyContinue
      Say "Downloading $(Split-Path $Path -Leaf), attempt $tryNo"
      Invoke-WebRequest -Uri $Url -OutFile $part -UseBasicParsing -MaximumRedirection 8
      if ($Hash -and (Get-FileHash -LiteralPath $part -Algorithm SHA256).Hash -ine $Hash) {
        throw 'Checksum mismatch; download discarded.'
      }
      Move-Item -LiteralPath $part -Destination $Path -Force
      return
    } catch {
      Remove-Item -LiteralPath $part -Force -ErrorAction SilentlyContinue
      if ($tryNo -eq 3) { throw "Cannot download $Url : $($_.Exception.Message)" }
      Start-Sleep -Seconds 2
    }
  }
}
function FindIde {
  if (!(Test-Path $IdeDir)) { return $null }
  $exe = Get-ChildItem -LiteralPath $IdeDir -Filter 'Arduino IDE.exe' -File -Recurse -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($exe) { return $exe.FullName }
  return $null
}
function IsAdmin {
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($id)
  return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}
New-Item -ItemType Directory -Force -Path $Root,$Cache,$Apps | Out-Null
try { Start-Transcript -Path (Join-Path $Root 'install.log') -Append -ErrorAction Stop | Out-Null } catch {}
try {
  if (![Environment]::Is64BitOperatingSystem) { throw 'Windows x64 is required.' }

  Say '1/5 Arduino IDE 2.3.10 (portable ZIP)'
  $ideExe = FindIde
  if (!$ideExe) {
    Fetch $IdeUrl $IdeZip $IdeSha256
    if (Test-Path $IdeDir) { Remove-Item -LiteralPath $IdeDir -Force -Recurse }
    New-Item -ItemType Directory -Force -Path $IdeDir | Out-Null
    Expand-Archive -LiteralPath $IdeZip -DestinationPath $IdeDir -Force
    $ideExe = FindIde
  }
  if (!$ideExe) { throw 'Arduino IDE executable was not found in ZIP.' }

  Say '2/5 Arduino CLI 1.5.1'
  if (!(Test-Path $Cli)) {
    Fetch $CliUrl $CliZip $CliSha256
    New-Item -ItemType Directory -Force -Path $CliDir | Out-Null
    Expand-Archive -LiteralPath $CliZip -DestinationPath $CliDir -Force
  }
  if (!(Test-Path $Cli)) { throw 'arduino-cli.exe was not found.' }
  & $Cli version
  if ($LASTEXITCODE -ne 0) { throw 'Arduino CLI version check failed.' }

  Say '3/5 ESP32 Core 3.3.12'
  $ArduinoData = Join-Path $env:LOCALAPPDATA 'Arduino15'
  New-Item -ItemType Directory -Force -Path $ArduinoData | Out-Null
  $Config = Join-Path $ArduinoData 'arduino-cli.yaml'
  if (!(Test-Path $Config)) {
    & $Cli config init
    if ($LASTEXITCODE -ne 0) { throw 'Failed to initialize Arduino CLI config.' }
  }
  $ConfigText = if (Test-Path $Config) { Get-Content $Config -Raw } else { '' }
  if ($ConfigText -notmatch [regex]::Escape($BoardUrl)) {
    & $Cli config add board_manager.additional_urls $BoardUrl
    if ($LASTEXITCODE -ne 0) { throw 'Failed to add Espressif board manager URL.' }
  }
  & $Cli core update-index
  if ($LASTEXITCODE -ne 0) { throw 'Failed to update Arduino board indexes.' }
  $CoreList = & $Cli core list
  if (($CoreList | Out-String) -notmatch 'esp32:esp32\s+3\.3\.12') {
    & $Cli core install 'esp32:esp32@3.3.12'
    if ($LASTEXITCODE -ne 0) { throw 'ESP32 Core installation failed.' }
  } else { Say 'ESP32 Core 3.3.12 already installed.' }

  Say '4/5 CP210x USB-to-UART driver'
  $Device = Get-PnpDevice -PresentOnly -ErrorAction SilentlyContinue |
    Where-Object { $_.InstanceId -like 'USB\VID_10C4&PID_EA60*' } | Select-Object -First 1
  if ($Device -and $Device.Status -eq 'OK') {
    Say 'CP210x device is already functioning.'
  } else {
    try {
      Fetch $DriverUrl $DriverZip
      if (!(Test-Path (Join-Path $DriverDir 'silabser.inf'))) {
        New-Item -ItemType Directory -Force -Path $DriverDir | Out-Null
        Expand-Archive -LiteralPath $DriverZip -DestinationPath $DriverDir -Force
      }
      $Inf = Get-ChildItem -LiteralPath $DriverDir -Recurse -Filter 'silabser.inf' -File |
        Select-Object -First 1
      if (!$Inf) { throw 'silabser.inf not found.' }
      if (IsAdmin) {
        & pnputil.exe /add-driver $Inf.FullName /install
        if ($LASTEXITCODE -ne 0) { throw 'Driver installation failed.' }
      } else {
        Say 'Driver installation needs UAC approval from an administrator.'
        $argText = '/add-driver "' + $Inf.FullName + '" /install'
        $proc = Start-Process pnputil.exe -ArgumentList $argText -Verb RunAs -Wait -PassThru
        if ($proc.ExitCode -ne 0) { throw 'Driver installer exited with an error.' }
      }
    } catch {
      Write-Warning "CP210x driver not installed: $($_.Exception.Message)"
      Write-Warning 'Contact school IT if you cannot approve driver installation.'
    }
  }
  Say '5/5 Compile SmartHomeCare sketch'
  & $Cli compile --fqbn esp32:esp32:esp32 $Sketch
  if ($LASTEXITCODE -ne 0) { throw 'Sketch compilation failed.' }
  Say 'IDE and ESP32 compiler are ready.'
  Say 'Choose Board: ESP32 Dev Module; choose the actual CP210x COM port.'
  Say 'USB uploading needs a functioning CP210x driver and a connected ESP32.'
  Start-Process -FilePath $ideExe -ArgumentList ('"' + (Join-Path $Sketch 'SmartHomeCare.ino') + '"')
  exit 0
} catch {
  Write-Host "[ERROR] $($_.Exception.Message)" -ForegroundColor Red
  exit 1
} finally {
  try { Stop-Transcript | Out-Null } catch {}
}
