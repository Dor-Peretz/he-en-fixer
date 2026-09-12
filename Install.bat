@echo off
setlocal
cd /d "%~dp0"

if exist "HE-EN Fixer\HE-EN Fixer.exe" (
  start "" "HE-EN Fixer\HE-EN Fixer.exe" --setup
  exit /b 0
)
if exist "HE-EN Fixer.exe" (
  start "" "HE-EN Fixer.exe" --setup
  exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" main.py --setup
  exit /b 0
)

where py >nul 2>nul
if %errorlevel%==0 (
  py -3 main.py --setup
  exit /b %errorlevel%
)

echo Python 3 is needed for this folder install.
echo Install it from https://www.python.org/downloads/
echo On the first screen, check "Add python.exe to PATH".
echo.
echo Or use the packaged Windows zip that includes Install.bat next to HE-EN Fixer.
pause
exit /b 1
