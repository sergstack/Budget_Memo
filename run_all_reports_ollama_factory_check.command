#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [ -d "${SCRIPT_DIR}/scripts" ]; then
  PROJECT_ROOT="$SCRIPT_DIR"
else
  PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
fi
VERIFIER_SCRIPT="${PROJECT_ROOT}/scripts/verify_accepted_ollama_report_packages.py"

cd "$PROJECT_ROOT"

if ! command -v python3 >/dev/null 2>&1; then
  echo "ERROR: python3 was not found in PATH."
  echo "Install or activate Python 3, then rerun this command."
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..."
  fi
  exit 1
fi

if [ ! -f "$VERIFIER_SCRIPT" ]; then
  echo "ERROR: verifier script not found: ${VERIFIER_SCRIPT}"
  if [ -t 0 ]; then
    read -r -p "Press Enter to close..."
  fi
  exit 1
fi

RUN_ID="$(date +%Y%m%d_%H%M%S)"
OUT_DIR="07_qa/accepted_packages_verification_${RUN_ID}"

mkdir -p "$OUT_DIR"

echo "Accepted memo package verifier"
echo "Project root: ${PROJECT_ROOT}"
echo "Verifier script: ${VERIFIER_SCRIPT}"
echo "Output folder: ${OUT_DIR}"
echo "Python: $(command -v python3)"
echo
echo "This command verifies accepted registry and QA artifacts only."
echo "It does not run Ollama, regenerate reports, render DOCX, rebuild marts, or read binary XLSX as text."
echo

python3 "$VERIFIER_SCRIPT" \
  --registry "06_reports/release_registry.xlsx" \
  --accepted-summary "06_reports/accepted_packages_summary.md" \
  --memo02-qa-dir "06_reports/02_monthly_plan_fact_memo/07_qa/factory_ollama_consensus_20260522_185632" \
  --output-dir "$OUT_DIR"

echo
echo "Summary:"
column -t -s $'\t' "${OUT_DIR}/run_summary.tsv" || cat "${OUT_DIR}/run_summary.tsv"
echo
echo "Done."
echo "QA folder: ${OUT_DIR}"
echo "Summary JSON: ${OUT_DIR}/run_summary.json"
echo "Summary TSV: ${OUT_DIR}/run_summary.tsv"
echo "Log: ${OUT_DIR}/run.log"
echo "Final status: pass"

if [ -t 0 ]; then
  read -r -p "Press Enter to close..."
fi
