@echo off
setlocal
cd /d "%~dp0"
set "PY=%LOCALAPPDATA%\ESP32SchoolKit\python-env\Scripts\python.exe"
if not exist "%PY%" (
 echo Run 00 common setup first.
 pause
 exit /b 1
)
"%PY%" "%~dp0manage-db.py" start
if errorlevel 1 goto fail
"%PY%" "%~dp0manage-db.py" selftest
if errorlevel 1 goto fail
echo Database verification successful.
pause
exit /b 0
:fail
echo Database verification failed.
pause
exit /b 1
