#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "${SCRIPT_DIR}/scripts" ]; then
  PROJECT_ROOT="$SCRIPT_DIR"
else
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
cd "$PROJECT_ROOT"

echo "Running stage pipeline..."
python3 src/main.py

echo
echo "Running mart generation..."
python3 src/build_marts.py

echo
echo "Done."

if [ -t 0 ]; then
  read -r -p "Press Enter to close..."
fi
