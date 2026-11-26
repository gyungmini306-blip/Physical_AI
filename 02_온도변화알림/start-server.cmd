@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\ESP32SchoolKit\python-env\Scripts\python.exe"
if not exist "%PY%" (
 echo Run common setup first.
 pause
 exit /b 1
)
"%PY%" "%~dp0MariaDB_설정\native_db.py" start
if errorlevel 1 (
 pause
 exit /b 1
)
"%PY%" -m serial.tools.list_ports
set "PORT="
set /p "PORT=Enter ESP32 COM port (blank for history only): "
echo Dashboard: http://127.0.0.1:5000
if defined PORT (
 "%PY%" "%~dp0server\app.py" --backend mariadb --open-browser --port "%PORT%"
) else (
 "%PY%" "%~dp0server\app.py" --backend mariadb --open-browser
)
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
