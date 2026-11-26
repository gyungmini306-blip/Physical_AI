@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
 echo Run setup-server.cmd first.
 pause
 exit /b 1
)
".venv\Scripts\python.exe" -m serial.tools.list_ports
set "PORT="
set /p "PORT=Enter ESP32 COM port (blank for history only): "
echo Dashboard: http://127.0.0.1:5000
if defined PORT (
 ".venv\Scripts\python.exe" server\app.py --port "%PORT%"
) else (
 ".venv\Scripts\python.exe" server\app.py
)
pause
