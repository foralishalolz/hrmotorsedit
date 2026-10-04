#!/bin/bash
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  python3 server.py --open
else
  echo "Python 3.10 or newer is required. Install it from https://www.python.org/downloads/"
fi
read -r -p "Press Enter to close this window. "
