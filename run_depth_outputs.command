#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "${SCRIPT_DIR}/scripts" ]; then
  PROJECT_ROOT="$SCRIPT_DIR"
else
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
cd "$PROJECT_ROOT"

echo "Generating memo depth outputs..."
python3 src/build_depth_mode_outputs.py

echo
echo "Done. Outputs are in 06_reports/01_executive_yoy_mom_budget_memo/."

if [ -t 0 ]; then
  read -r -p "Press Enter to close..."
fi
