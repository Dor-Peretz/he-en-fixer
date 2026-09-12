#!/bin/bash
set -e
cd "$(dirname "$0")"

if [ -d "HE-EN Fixer.app" ]; then
  open "HE-EN Fixer.app" --args --setup
  exit 0
fi

if [ -x "HE-EN Fixer.app/Contents/MacOS/HE-EN Fixer" ]; then
  "HE-EN Fixer.app/Contents/MacOS/HE-EN Fixer" --setup
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
