#!/bin/sh
cd "$(dirname "$0")" || exit 1
if command -v python3 >/dev/null 2>&1; then
  exec python3 server.py --open "$@"
else
  echo "Python 3.10 or newer is required. Install Python and try again."
  exit 1
fi
