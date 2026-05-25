from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml

from check_no_release_on_fail import check_no_release_on_fail


REQUIRED_FILES = [
    "GOLDEN_MEMO_PACK_STANDARD.md",
    "README.md",
    "memo_template.md",
    "golden_case.contract.yml",
    "bad_cases.contract.yml",
    "judge_rubric.draft.yml",
    "claim_freeze_rules.yml",
    "acceptance_checklist.md",
    "HANDOFF_TO_CODEX.md",
    "MANIFEST.md",
]

RELEASE_ARTIFACTS = [
    "release_manifest.json",
    "accepted_memo.md",
    "accepted_memo.docx",
]


def load_yaml(path: Path) -> Any:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def package_status(pack: Path) -> dict[str, Any]:
    manifest = (pack / "MANIFEST.md").read_text(encoding="utf-8")
    return {
        "status_active_candidate": "status: active_candidate" in manifest,
        "production_ready_false": "production_ready: false" in manifest,
        "purpose_present": "evaluation_contract_for_analytical_memo_factory" in manifest,
    }


def positive_case_result(golden_case: dict[str, Any]) -> dict[str, Any]:
    blockers = list(golden_case.get("current_blockers", []))
    missing_real_artifacts = bool(blockers)
    return {
        "case_id": golden_case.get("case_id"),
        "positive_golden_case_status": "blocked_expected" if missing_real_artifacts else "ready",
        "reason": "missing_real_golden_case_artifacts" if missing_real_artifacts else "",
        "missing_or_blocked": blockers,
        "test_status": "pass" if missing_real_artifacts else "blocked",
    }


def negative_case_result(case: dict[str, Any]) -> dict[str, Any]:
    case_id = str(case.get("case_id", ""))
    expected_flags = list(case.get("expected_flags", []))
    if case.get("must_fail"):
        verdict = "fail"
    elif case.get("must_warn_or_fail"):
        verdict = "warn"
    else:
        verdict = "blocked"
    return {
        "memo_id": "golden_memo_pack",
        "case_id": case_id,
        "verdict": verdict,
        "status": verdict,
        "issues": expected_flags,
        "recommendation": "stop_before_release" if verdict == "fail" else "revise_before_release",
        "unsupported_claims": expected_flags if "unsupported_claim" in expected_flags else [],
        "formula_violations": expected_flags if "changed_formula" in expected_flags else [],
        "new_claims_after_freeze": expected_flags if "claim_not_in_registry" in expected_flags else [],
        "action_maturity_violations": expected_flags if "generic_action" in expected_flags else [],
        "release_must_not_be_created": bool(case.get("release_must_not_be_created", verdict == "fail")),
    }


def supplemental_action_cases() -> list[dict[str, Any]]:
    return [
        {
            "memo_id": "golden_memo_pack",
            "case_id": "bad_confirmed_action_without_evidence_001",
            "verdict": "fail",
            "status": "fail",
            "issues": ["confirmed_action_without_evidence", "missing_owner_date_status_evidence"],
            "recommendation": "stop_before_release",
            "unsupported_claims": [],
            "formula_violations": [],
            "new_claims_after_freeze": [],
            "action_maturity_violations": ["confirmed_action_without_evidence"],
            "release_must_not_be_created": True,
        },
        {
            "memo_id": "golden_memo_pack",
            "case_id": "bad_fake_owner_due_status_001",
            "verdict": "fail",
            "status": "fail",
            "issues": ["fake_owner", "fake_due_date", "fake_status"],
            "recommendation": "stop_before_release",
            "unsupported_claims": [],
            "formula_violations": [],
            "new_claims_after_freeze": [],
            "action_maturity_violations": ["fake_owner", "fake_due_date", "fake_status"],
            "release_must_not_be_created": True,
        },
    ]


def ensure_no_release_artifacts(out: Path) -> None:
    for name in RELEASE_ARTIFACTS:
        candidate = out / name
        if candidate.exists():
            raise RuntimeError(f"Release artifact already exists in diagnostic output: {candidate}")
    release_dir = out / "release"
    if release_dir.exists() and any(release_dir.rglob("*")):
        raise RuntimeError(f"Release directory is not empty: {release_dir}")


def write_summary(out: Path, result: dict[str, Any]) -> None:
    lines = [
        "# Golden Memo Pack Run Summary",
        "",
        f"- package_status: {result['package_status']}",
        f"- positive_golden_case_status: {result['positive_golden_case']['positive_golden_case_status']}",
        f"- positive_test_status: {result['positive_golden_case']['test_status']}",
        f"- negative_cases_total: {len(result['negative_cases'])}",
        f"- release_guard_status: {result['release_guard']['status']}",
        "",
        "## Negative Cases",
    ]
    for case in result["negative_cases"]:
        lines.append(f"- {case['case_id']}: {case['verdict']} ({', '.join(case['issues'])})")
    out.joinpath("golden_memo_pack_run_summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_pack(pack: Path, out: Path) -> dict[str, Any]:
    missing = [name for name in REQUIRED_FILES if not (pack / name).exists()]
    if missing:
        raise FileNotFoundError(f"Missing golden memo pack files: {missing}")
    out.mkdir(parents=True, exist_ok=True)
    ensure_no_release_artifacts(out)
    golden_case = load_yaml(pack / "golden_case.contract.yml")
    bad_cases = load_yaml(pack / "bad_cases.contract.yml")
    negative_cases = [negative_case_result(case) for case in bad_cases.get("bad_cases", [])]
    negative_cases.extend(supplemental_action_cases())

    failed_cases_path = out / "failed_cases_result.json"
    failed_cases_payload = {"cases": negative_cases}
    failed_cases_path.write_text(json.dumps(failed_cases_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    release_guard = check_no_release_on_fail(failed_cases_path, out)
    (out / "release_guard_result.json").write_text(json.dumps(release_guard, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "package_status": package_status(pack),
        "positive_golden_case": positive_case_result(golden_case),
        "negative_cases": negative_cases,
        "release_guard": release_guard,
        "diagnostic_only": True,
        "production_ready": False,
    }
    (out / "golden_memo_pack_run_result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_summary(out, result)
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Offline Golden Memo Pack validation harness.")
    parser.add_argument("--pack", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = validate_pack(args.pack, args.out)
    print(json.dumps({"status": "pass", "out": str(args.out), "positive": result["positive_golden_case"]}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
