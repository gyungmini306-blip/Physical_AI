@echo off
setlocal
set "CLI=%LOCALAPPDATA%\ESP32SchoolKit\apps\arduino-cli\arduino-cli.exe"
if not exist "%CLI%" (
  echo Arduino CLI not installed. Run setup.cmd first.
  pause
  exit /b 1
)
echo.
echo [1/3] SmartHomeCare (original)
"%CLI%" compile --fqbn esp32:esp32:esp32 "%~dp0sketches\SmartHomeCare"
if errorlevel 1 (
  echo Original sketch compilation FAILED.
  pause
  exit /b 1
)
echo.
echo [2/3] SmartHomeCarePlus (Wi-Fi dashboard)
"%CLI%" compile --fqbn esp32:esp32:esp32 "%~dp0sketches\SmartHomeCarePlus"
if errorlevel 1 (
  echo PLUS sketch compilation FAILED.
  pause
  exit /b 1
)
echo.
echo.
echo [3/3] SmartHomeCarePlusBuzzer (latched alarm)
"%CLI%" compile --fqbn esp32:esp32:esp32 "%~dp0sketches\SmartHomeCarePlusBuzzer"
if errorlevel 1 (
  echo Buzzer sketch compilation FAILED.
  pause
  exit /b 1
)
echo.
echo All three sketches compiled successfully.
pause
exit /b 0
