@echo off
setlocal
cd /d "%~dp0"
docker compose exec db mariadb -u temperature_app -p temperature_alert
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
