@echo off
setlocal
cd /d "%~dp0"
docker compose ps
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
