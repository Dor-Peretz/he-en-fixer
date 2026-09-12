#!/bin/bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
STAGE="$ROOT/release/HE-EN-Fixer-macOS"
ZIP="$ROOT/release/HE-EN-Fixer-macOS.zip"
BUILT="$ROOT/dist/HE-EN Fixer.app"
if [ ! -d "$BUILT" ]; then
  BUILT="$ROOT/dist/HE-EN Fixer/HE-EN Fixer.app"
fi
if [ ! -d "$BUILT" ]; then
  echo "Build output missing" >&2
  exit 1
fi
rm -rf "$STAGE"
mkdir -p "$STAGE"
cp -R "$BUILT" "$STAGE/HE-EN Fixer.app"
cp "$ROOT/Install.command" "$STAGE/"
cp "$ROOT/Uninstall.command" "$STAGE/"
cp "$ROOT/README.md" "$STAGE/"
chmod +x "$STAGE/Install.command" "$STAGE/Uninstall.command"
cat > "$STAGE/HOW TO INSTALL.txt" <<'EOF'
HE-EN Fixer
===========

1. Double-click Install.command
2. Click Install
3. Allow Accessibility in System Settings → Privacy & Security
4. Click Open app

This installs only for your Mac user account.
It does not need an administrator password for the copy into your home folder.
It does not send your typing to the internet.

To remove it, double-click Install.command and click Uninstall.
EOF
mkdir -p "$ROOT/release"
rm -f "$ZIP"
ditto -c -k --keepParent "$STAGE" "$ZIP"
echo "Created $ZIP"
