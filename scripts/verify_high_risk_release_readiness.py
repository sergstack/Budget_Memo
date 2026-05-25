from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


REQUIRED_CHECKS = [
    "scope_fixed",
    "data_contract_passed",
    "mart_verification_passed",
    "formula_checks_passed",
    "claim_registry_exists",
    "critical_claims_have_evidence_id",
    "claim_freeze_diff_passed",
    "evidence_judge_passed",
    "finance_or_logic_judge_passed",
    "russian_language_judge_passed",
    "management_readability_judge_passed",
    "docx_media_count_passed",
    "libreoffice_render_passed",
    "release_manifest_exists",
    "human_review_required_or_pending",
    "learning_note_saved_after_non_trivial_fix",
]


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def verify_readiness(input_path: Path) -> dict[str, Any]:
    data = load_json(input_path)
    checks = data.get("checks", {})
    blockers = [name for name in REQUIRED_CHECKS if checks.get(name) is not True]
    status = "pass" if not blockers else "blocked"
    return {
        "status": status,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "memo_id": data.get("memo_id", ""),
        "blockers": blockers,
        "warnings": data.get("warnings", []),
        "required_checks": REQUIRED_CHECKS,
    }


def write_markdown(path: Path, result: dict[str, Any]) -> None:
    lines = [
        "# High-Risk Release Readiness",
        "",
        f"- memo_id: {result.get('memo_id', '')}",
        f"- status: {result['status']}",
        "",
        "## Blockers",
    ]
    lines.extend(f"- {item}" for item in result["blockers"])
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify high-risk memo release readiness without running generation.")
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--out-json", required=True, type=Path)
    parser.add_argument("--out-md", required=True, type=Path)
    args = parser.parse_args()
    result = verify_readiness(args.input)
    args.out_json.parent.mkdir(parents=True, exist_ok=True)
    args.out_json.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(args.out_md, result)
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
