from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


RELEASE_NAMES = {
    "release_manifest.json",
    "accepted_memo.md",
    "accepted_memo.docx",
}


def load_cases(path: Path) -> list[dict[str, Any]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if isinstance(data, dict):
        return list(data.get("cases", data.get("failed_cases_checked", [])))
    return list(data)


def check_no_release_on_fail(cases_path: Path, artifacts_root: Path) -> dict[str, Any]:
    cases = load_cases(cases_path)
    failed = [case for case in cases if case.get("status") in {"fail", "blocked"} or case.get("verdict") in {"fail", "blocked"}]
    violations = []
    for case in failed:
        case_id = str(case.get("case_id", ""))
        case_dir = artifacts_root / case_id
        candidates = []
        if case_dir.exists():
            candidates.extend(path for path in case_dir.rglob("*") if path.is_file())
        release_dir = artifacts_root / "release"
        if release_dir.exists():
            candidates.extend(path for path in release_dir.rglob("*") if path.is_file())
        for path in candidates:
            if path.name in RELEASE_NAMES or "release_registry" in path.name or "artifacts/release" in str(path):
                violations.append({"case_id": case_id, "path": str(path)})
    return {
        "status": "fail" if violations else "pass",
        "failed_cases_checked": [case.get("case_id") for case in failed],
        "release_artifact_violations": violations,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Ensure failed golden memo cases do not produce release artifacts.")
    parser.add_argument("--cases", required=True, type=Path)
    parser.add_argument("--artifacts-root", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = check_no_release_on_fail(args.cases, args.artifacts_root)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
