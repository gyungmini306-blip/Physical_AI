@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>&1
if errorlevel 1 (
 echo Python 3.10+ is required. Install Python from python.org first.
 pause
 exit /b 1
)
py -3 -c "import sys; assert sys.version_info >= (3,10)"
if errorlevel 1 goto fail
py -3 -m venv .venv
if errorlevel 1 goto fail
".venv\Scripts\python.exe" -m pip install -r server\requirements.txt
if errorlevel 1 goto fail
echo Server setup complete.
pause
exit /b 0
:fail
echo Server setup failed.
pause
exit /b 1
