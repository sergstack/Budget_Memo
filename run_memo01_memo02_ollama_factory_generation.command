#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "${SCRIPT_DIR}/scripts" ]; then
  PROJECT_ROOT="$SCRIPT_DIR"
else
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
GENERATOR_SCRIPT="${PROJECT_ROOT}/scripts/regenerate_memo01_memo02_ollama_factory.py"
OLLAMA_ENDPOINT="${OLLAMA_ENDPOINT:-http://127.0.0.1:11434}"
SOFFICE="/Applications/LibreOffice.app/Contents/MacOS/soffice"

cd "$PROJECT_ROOT"

echo "Memo01 + Memo02 Ollama factory generation"
echo "Project root: ${PROJECT_ROOT}"
echo "Generator script: ${GENERATOR_SCRIPT}"
echo "Ollama endpoint: ${OLLAMA_ENDPOINT}"
echo "LibreOffice: ${SOFFICE}"
echo "Active memos:"
echo "  - 06_reports/01_executive_yoy_mom_budget_memo/"
echo "  - 06_reports/02_monthly_plan_fact_memo/"
echo
echo "This is REAL generation unless you pass --dry-run."
echo "It runs memo01 first, then memo02. No parallel Ollama jobs."
echo

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 was not found in PATH."
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..."
  fi
  exit 1
fi

if [ ! -f "$GENERATOR_SCRIPT" ]; then
  echo "ERROR: generator script not found: ${GENERATOR_SCRIPT}"
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..."
  fi
  exit 1
fi

if [ ! -x "$SOFFICE" ]; then
  echo "ERROR: LibreOffice soffice was not found or is not executable: ${SOFFICE}"
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..."
  fi
  exit 1
fi

if pgrep -af "[s]cripts/regenerate_memo01_memo02_ollama_factory.py" >/dev/null; then
  echo "ERROR: generation is already running. Refusing to start a parallel Ollama job."
  pgrep -af "[s]cripts/regenerate_memo01_memo02_ollama_factory.py" || true
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..."
  fi
  exit 1
fi

GENERATOR_HELP="$(python3 "$GENERATOR_SCRIPT" --help)"
if [ "${1:-}" = "--dry-run" ] && ! printf "%s\n" "$GENERATOR_HELP" | grep -q -- "--dry-run"; then
  echo "ERROR: dry-run not available; generation not run."
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..."
  fi
  exit 1
fi

if [ "${1:-}" != "--dry-run" ]; then
  python3 - <<PY
import urllib.request
urllib.request.urlopen("${OLLAMA_ENDPOINT}/api/tags", timeout=5).read()
print("Ollama endpoint: ok")
PY
fi

echo "Starting generator..."
echo

python3 "$GENERATOR_SCRIPT" "$@"

echo
echo "Running accepted-package verification after generation..."
./run_all_reports_ollama_factory_check.command

echo
echo "Final status: pass"

if [ -t 0 ]; then
  read -r -p "Press Enter to close..."
fi
