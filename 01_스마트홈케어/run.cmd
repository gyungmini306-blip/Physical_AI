@echo off
setlocal
cd /d "%~dp0"
title Smart Home Care
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup\ensure.ps1"
if errorlevel 1 goto fail
set "PY=%LOCALAPPDATA%\ESP32SchoolKit\python-env\Scripts\python.exe"
"%PY%" "%~dp0launch.py" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" pause
exit /b %RESULT%
:fail
echo Environment setup failed. Review the messages above.
pause
exit /b 1
