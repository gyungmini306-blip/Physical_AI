@echo off
setlocal
cd /d "%~dp0"
powershell.exe -NoProfile -File "%~dp0setup-db.ps1"
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
