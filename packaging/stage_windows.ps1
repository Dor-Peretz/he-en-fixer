$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$stage = Join-Path $root "release\HE-EN-Fixer-Windows"
$zip = Join-Path $root "release\HE-EN-Fixer-Windows.zip"
$built = Join-Path $root "dist\HE-EN Fixer"

if (-not (Test-Path $built)) {
    throw "Build output missing: $built"
}

New-Item -ItemType Directory -Force -Path (Join-Path $root "release") | Out-Null
if (Test-Path $stage) { Remove-Item $stage -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stage | Out-Null

Copy-Item $built (Join-Path $stage "HE-EN Fixer") -Recurse
Copy-Item (Join-Path $root "Install.bat") $stage
Copy-Item (Join-Path $root "Uninstall.bat") $stage
Copy-Item (Join-Path $root "README.md") $stage
Set-Content -Path (Join-Path $stage "HOW TO INSTALL.txt") -Encoding UTF8 -Value @"
HE-EN Fixer
===========

1. Double-click Install.bat
2. Click Install
3. Click Open app

This installs only for your Windows user account.
It does not need administrator permission.
It does not send your typing to the internet.

To remove it, double-click Install.bat again and click Uninstall.
"@

if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $stage -DestinationPath $zip
Write-Host "Created $zip"
