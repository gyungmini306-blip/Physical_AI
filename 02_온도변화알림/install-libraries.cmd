@echo off
setlocal
set "CLI=%LOCALAPPDATA%\ESP32SchoolKit\apps\arduino-cli\arduino-cli.exe"
if not exist "%CLI%" (
 echo Arduino CLI not found. Run the common setup first.
 pause
 exit /b 1
)
"%CLI%" lib update-index
if errorlevel 1 goto fail
"%CLI%" lib install "DHT sensor library" "Adafruit Unified Sensor"
if errorlevel 1 goto fail
echo Library installation complete.
pause
exit /b 0
:fail
echo Library installation failed.
pause
exit /b 1
