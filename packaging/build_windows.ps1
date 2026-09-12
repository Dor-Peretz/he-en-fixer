$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$py = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $py)) {
    py -3 -m venv (Join-Path $root ".venv")
}
& $py -m pip install --upgrade pip
& $py -m pip install -r (Join-Path $root "requirements.txt") pyinstaller
& $py (Join-Path $root "packaging\make_icon.py")
& (Join-Path $root ".venv\Scripts\pyinstaller.exe") --noconfirm (Join-Path $root "he-en-fixer.spec")
powershell -File (Join-Path $root "packaging\stage_windows.ps1")
Write-Host "Give people this file: $root\release\HE-EN-Fixer-Windows.zip"
