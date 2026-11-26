@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup-all.ps1"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
