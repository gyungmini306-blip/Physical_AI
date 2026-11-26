@echo off
setlocal
cd /d "%~dp0"
title Temperature Alert - USB / MariaDB / Dashboard
set "PY=%LOCALAPPDATA%\ESP32SchoolKit\python-env\Scripts\python.exe"
if not exist "%PY%" (
 echo First-time setup required: 00_ Arduino setup.cmd
 pause
 exit /b 1
)
"%PY%" "%~dp0launch.py" %*
set "RESULT=%ERRORLEVEL%"
if not "%RESULT%"=="0" (
 echo Startup failed. See error above.
 pause
)
exit /b %RESULT%
