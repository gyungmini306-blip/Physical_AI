@echo off
setlocal
set "CLI=%LOCALAPPDATA%\ESP32SchoolKit\apps\arduino-cli\arduino-cli.exe"
if not exist "%CLI%" (
  echo Arduino CLI not installed. Run setup.cmd first.
  exit /b 1
)
set "SKETCH=%~dp0sketches\SetupCheck"
if not "%~1"=="" set "SKETCH=%~f1"
"%CLI%" compile --fqbn esp32:esp32:esp32 "%SKETCH%"
set "RESULT=%ERRORLEVEL%"
if "%RESULT%"=="0" (echo Compilation succeeded.) else (echo Compilation failed.)
exit /b %RESULT%
