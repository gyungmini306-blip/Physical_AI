@echo off
setlocal
set "CLI=%LOCALAPPDATA%\ESP32SchoolKit\apps\arduino-cli\arduino-cli.exe"
if not exist "%CLI%" (
  echo Arduino CLI not installed. Run setup.cmd first.
  pause
  exit /b 1
)
echo.
echo [1/2] SmartHomeCare (original)
"%CLI%" compile --fqbn esp32:esp32:esp32 "%~dp0sketches\SmartHomeCare"
if errorlevel 1 (
  echo Original sketch compilation FAILED.
  pause
  exit /b 1
)
echo.
echo [2/2] SmartHomeCarePlus (Wi-Fi dashboard)
"%CLI%" compile --fqbn esp32:esp32:esp32 "%~dp0sketches\SmartHomeCarePlus"
if errorlevel 1 (
  echo PLUS sketch compilation FAILED.
  pause
  exit /b 1
)
echo.
echo Both sketches compiled successfully.
pause
exit /b 0
