@echo off
setlocal
cd /d "%~dp0"

if exist "HE-EN Fixer\HE-EN Fixer.exe" (
  start "" "HE-EN Fixer\HE-EN Fixer.exe" --setup
  exit /b 0
)
if exist ".venv\Scripts\pythonw.exe" (
  start "" ".venv\Scripts\pythonw.exe" main.py --setup
  exit /b 0
)
if exist "Install.bat" (
  call Install.bat
  exit /b %errorlevel%
)

echo Open Install.bat and click Uninstall there.
pause
