@echo off
setlocal
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\ESP32SchoolKit\python-env\Scripts\python.exe"
if not exist "%PY%" (
 echo Run common setup first.
 pause
 exit /b 1
)
"%PY%" "%~dp0manage-db.py" stop
set "RESULT=%ERRORLEVEL%"
pause
exit /b %RESULT%
