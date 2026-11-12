@echo off
setlocal
set "CLI=%LOCALAPPDATA%\ESP32SchoolKit\apps\arduino-cli\arduino-cli.exe"
if not exist "%CLI%" (
  echo Arduino CLI not installed. Run setup.cmd first.
  pause
  exit /b 1
)
"%CLI%" core list
echo.
"%CLI%" compile --fqbn esp32:esp32:esp32 "%~dp0sketches\SmartHomeCare"
set "RESULT=%ERRORLEVEL%"
if "%RESULT%"=="0" (echo COMPILE OK) else (echo COMPILE FAILED)
pause
exit /b %RESULT%
