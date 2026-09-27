#!/bin/bash
set -e
cd "$(dirname "$0")"

APP="HE-EN Fixer.app"

if [ -d "$APP" ]; then
  # Files extracted from a downloaded zip inherit its quarantine flag. Once the
  # user has approved this installer, clear that flag from the bundled app so
  # macOS does not block the installer window or the installed copy again.
  /usr/bin/xattr -dr com.apple.quarantine "$APP" 2>/dev/null || true
  if open "$APP" --args --setup; then
    exit 0
  fi
fi

if [ -x "$APP/Contents/MacOS/HE-EN Fixer" ]; then
  "$APP/Contents/MacOS/HE-EN Fixer" --setup
  exit 0
fi

if [ -x ".venv/bin/python" ]; then
  ".venv/bin/python" main.py --setup
  exit 0
fi

if command -v python3 >/dev/null 2>&1; then
  python3 main.py --setup
  exit 0
fi

echo "Python 3 is needed. Install it from https://www.python.org/downloads/macos/"
echo "After installing, double-click this file again."
read -r _
exit 1
