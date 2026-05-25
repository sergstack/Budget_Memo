from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "docs/test_strategy_matrix.md",
    "docs/ci_matrix.md",
    "docs/local_regression_plan.md",
    "docs/artifact_validation_matrix.md",
    "docs/performance_refactor_gate.md",
}

REQUIRED_MARKERS = {
    "TESTING.md": [
        "docs/test_strategy_matrix.md",
        "docs/ci_matrix.md",
        "docs/local_regression_plan.md",
        "docs/artifact_validation_matrix.md",
        "docs/performance_refactor_gate.md",
        "not the default public CI command",
    ],
    "docs/developer_workflow.md": [
        "docs/test_strategy_matrix.md",
        "docs/ci_matrix.md",
        "docs/local_regression_plan.md",
        "docs/artifact_validation_matrix.md",
        "docs/performance_refactor_gate.md",
    ],
    "docs/reviewer_quickstart.md": [
        "docs/test_strategy_matrix.md",
        "docs/ci_matrix.md",
    ],
    "docs/test_strategy_matrix.md": [
        "public_data_free",
        "local_data_dependent",
        "report_generation",
        "ollama_live_llm",
        "contract_regression",
        "performance_future",
        "docs/local_regression_plan.md",
        "docs/artifact_validation_matrix.md",
        "docs/performance_refactor_gate.md",
        "Full `python3 -m unittest discover -s tests -q` is not public-data-free by default.",
    ],
    "docs/ci_matrix.md": [
        "current GitHub Actions workflow",
        "public_data_free",
        "Local regression lanes are documented but not activated in GitHub CI.",
        "docs/local_regression_plan.md",
        "docs/artifact_validation_matrix.md",
        "docs/performance_refactor_gate.md",
        "python scripts/check_test_strategy.py",
        "python -m unittest tests.test_test_strategy -q",
    ],
    "docs/local_regression_plan.md": [
        "stage_contract_validation",
        "mart_contract_validation",
        "report_artifact_validation",
        "render_docx_pdf_validation",
        "ollama_live_llm_validation",
        "end_to_end_local_smoke",
        "must not run in GitHub public CI",
        "require explicit task authorization",
    ],
    "docs/artifact_validation_matrix.md": [
        "These artifact folders are local/ignored and must not be committed.",
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
    ],
    "docs/performance_refactor_gate.md": [
        "low_risk_docs_or_checker_only",
        "medium_risk_pipeline_io",
        "high_risk_formula_or_schema",
        "blocked_without_business_approval",
        "Data-free checks pass.",
        "Local regression checks are selected if the change is data-dependent.",
    ],
}

DISALLOWED_WORKFLOW_MARKERS = {
    "src/main.py",
    "src/build_marts.py",
    "python3 -m unittest discover",
    "python -m unittest discover",
    "unittest discover -s tests",
    "regenerate_memo01_memo02_ollama_factory.py",
    "run_ollama_memo_pipeline.py",
    "build_depth_mode_outputs.py",
    "build_report.py",
    "build_docx_report.py",
    "verify_accepted_ollama_report_packages.py",
    "local_regression_plan.md",
    "artifact_validation_matrix.md",
    "performance_refactor_gate.md",
}

REQUIRED_WORKFLOW_MARKERS = {
    "python scripts/check_repo_public_safety.py",
    "python -m unittest tests.test_repo_public_safety -q",
    "python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml",
    "python scripts/check_test_strategy.py",
    "python -m unittest tests.test_test_strategy -q",
}


def read_repo_file(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def check_required_files() -> list[str]:
    return sorted(path for path in REQUIRED_FILES if not (ROOT / path).exists())


def check_text_markers() -> dict[str, list[str]]:
    missing: dict[str, list[str]] = {}
    for path, markers in REQUIRED_MARKERS.items():
        file_path = ROOT / path
        if not file_path.exists():
            missing[path] = list(markers)
            continue
        text = file_path.read_text(encoding="utf-8")
        missing_markers = [marker for marker in markers if marker not in text]
        if missing_markers:
            missing[path] = missing_markers
    return missing


def workflow_disallowed_markers(text: str) -> list[str]:
    return sorted(marker for marker in DISALLOWED_WORKFLOW_MARKERS if marker in text)


def workflow_missing_required_markers(text: str) -> list[str]:
    return sorted(marker for marker in REQUIRED_WORKFLOW_MARKERS if marker not in text)


def check_workflow() -> dict[str, list[str]]:
    workflow = read_repo_file(".github/workflows/repo-smoke.yml")
    return {
        "disallowed": workflow_disallowed_markers(workflow),
        "missing_required": workflow_missing_required_markers(workflow),
    }


def main() -> int:
    missing_files = check_required_files()
    missing_markers = check_text_markers()
    workflow = check_workflow()

    blockers: list[str] = []
    if missing_files:
        blockers.append("missing_required_files")
    if missing_markers:
        blockers.append("missing_text_markers")
    if workflow["disallowed"]:
        blockers.append("workflow_runs_disallowed_commands")
    if workflow["missing_required"]:
        blockers.append("workflow_missing_required_commands")

    result = {
        "status": "fail" if blockers else "pass",
        "missing_required_files": missing_files,
        "missing_text_markers": missing_markers,
        "workflow_disallowed_markers": workflow["disallowed"],
        "workflow_missing_required_markers": workflow["missing_required"],
        "blockers": blockers,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
