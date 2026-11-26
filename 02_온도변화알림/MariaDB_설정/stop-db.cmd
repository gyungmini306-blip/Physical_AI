@echo off
setlocal
cd /d "%~dp0"
docker compose stop db
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
