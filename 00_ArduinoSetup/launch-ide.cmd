@echo off
setlocal
powershell.exe -NoProfile -Command "$p=Join-Path $env:LOCALAPPDATA 'ESP32SchoolKit\apps\arduino-ide'; $exe=Get-ChildItem -LiteralPath $p -Recurse -Filter 'Arduino IDE.exe' -File -ErrorAction SilentlyContinue | Select-Object -First 1; if($exe){ Start-Process $exe.FullName } else { Write-Host 'Arduino IDE not found. Run setup.cmd first.'; exit 1 }"
if errorlevel 1 pause
