@echo off
setlocal
cd /d "%~dp0"
echo ====================================================
echo ESP32 school setup - Arduino IDE / CLI / ESP32 / CP210x
echo ====================================================
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0setup.ps1"
set "RESULT=%ERRORLEVEL%"
echo.
if "%RESULT%"=="0" (
 echo Setup complete. Select ESP32 Dev Module and the CP210x COM port in Arduino IDE.
) else (
 echo Setup failed. Check the messages above.
)
echo Press any key to close.
pause >nul
exit /b %RESULT%
