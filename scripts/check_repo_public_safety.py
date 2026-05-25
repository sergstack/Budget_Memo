from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

FORBIDDEN_DIRS = {
    "01_raw/",
    "02_stage/",
    "03_marts/",
    "04_charts/",
    "04_signals/",
    "05_evidence/",
    "05_llm_package/",
    "06_reports/",
    "07_qa/",
    "99_archive/",
    "artifacts/",
    "output/",
    "outputs/",
    "logs/",
    "tmp/",
    "temp/",
    ".cache/",
}

FORBIDDEN_SUFFIXES = {
    ".xlsx",
    ".xls",
    ".xlsm",
    ".csv",
    ".tsv",
    ".parquet",
    ".feather",
    ".jsonl",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".pkl",
    ".zip",
    ".7z",
    ".rar",
    ".docx",
    ".pdf",
    ".png",
    ".log",
    ".pem",
    ".key",
    ".p12",
    ".pfx",
}

REQUIRED_TOP_LEVEL = {
    ".env.example",
    ".gitignore",
    "README.md",
    "AGENTS.md",
    "TESTING.md",
    "requirements.txt",
}

REQUIRED_GITIGNORE_PATTERNS = {
    ".env",
    ".env.*",
    "!.env.example",
    "01_raw/",
    "02_stage/",
    "03_marts/",
    "04_charts/",
    "04_signals/",
    "05_evidence/",
    "05_llm_package/",
    "06_reports/",
    "07_qa/",
    "99_archive/",
    "artifacts/",
    "*.xlsx",
    "*.csv",
    "*.parquet",
    "*.docx",
    "*.pdf",
    "*.png",
    "*.log",
}


def run_git_ls_files() -> list[str]:
    result = subprocess.run(
        ["git", "ls-files"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or "git ls-files failed")
    return [line for line in result.stdout.splitlines() if line]


def is_forbidden_tracked_file(path: str) -> bool:
    if path == ".env":
        return True
    if path == ".env.example":
        return False
    if any(path.startswith(prefix) for prefix in FORBIDDEN_DIRS):
        return True
    suffix = Path(path).suffix.lower()
    return suffix in FORBIDDEN_SUFFIXES


def check_required_files() -> list[str]:
    return sorted(path for path in REQUIRED_TOP_LEVEL if not (ROOT / path).exists())


def check_gitignore_patterns() -> list[str]:
    gitignore = ROOT / ".gitignore"
    if not gitignore.exists():
        return sorted(REQUIRED_GITIGNORE_PATTERNS)
    patterns = {
        line.strip()
        for line in gitignore.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    }
    return sorted(REQUIRED_GITIGNORE_PATTERNS - patterns)


def main() -> int:
    blockers: list[str] = []
    tracked = run_git_ls_files()
    forbidden = sorted(path for path in tracked if is_forbidden_tracked_file(path))
    missing_required = check_required_files()
    missing_gitignore = check_gitignore_patterns()

    if forbidden:
        blockers.append("forbidden_tracked_files")
    if missing_required:
        blockers.append("missing_required_files")
    if ".env" in tracked:
        blockers.append("env_file_tracked")
    if ".env.example" not in tracked and not (ROOT / ".env.example").exists():
        blockers.append("missing_env_example")
    if missing_gitignore:
        blockers.append("missing_gitignore_patterns")
    if not (ROOT / "config/memo_factory_quality_gates.yml").exists():
        blockers.append("missing_quality_gates_config")

    result = {
        "status": "fail" if blockers else "pass",
        "tracked_files_count": len(tracked),
        "forbidden_tracked_files": forbidden,
        "missing_required_files": missing_required,
        "missing_gitignore_patterns": missing_gitignore,
        "blockers": blockers,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
