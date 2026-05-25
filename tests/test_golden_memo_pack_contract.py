from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
PACK = ROOT / "99_docs/golden_memo_pack"
ARTIFACTS = ROOT / "artifacts/golden_memo_pack"


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_golden_pack_files_exist() -> None:
    expected = [
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
    for name in expected:
        assert (PACK / name).exists(), name


def test_positive_case_is_blocked_expected_when_real_artifacts_missing(tmp_path: Path) -> None:
    out = tmp_path / "out"
    result = run_cmd([sys.executable, "scripts/validate_golden_memo_pack.py", "--pack", str(PACK), "--out", str(out)])
    assert result.returncode == 0, result.stderr
    payload = load_json(out / "golden_memo_pack_run_result.json")
    assert payload["positive_golden_case"]["positive_golden_case_status"] == "blocked_expected"
    assert payload["positive_golden_case"]["reason"] == "missing_real_golden_case_artifacts"
    assert payload["positive_golden_case"]["test_status"] == "pass"


def test_unsupported_claim_case_fails() -> None:
    payload = load_json(ARTIFACTS / "failed_cases_result.json")
    case = next(item for item in payload["cases"] if item["case_id"] == "bad_unsupported_claim_001")
    assert case["verdict"] == "fail"
    assert "unsupported_claim" in case["issues"]


def test_formula_change_case_fails() -> None:
    payload = load_json(ARTIFACTS / "failed_cases_result.json")
    case = next(item for item in payload["cases"] if item["case_id"] == "bad_formula_change_001")
    assert case["verdict"] == "fail"
    assert "changed_formula" in case["issues"]


def test_new_claim_after_freeze_fails() -> None:
    payload = load_json(ARTIFACTS / "failed_cases_result.json")
    case = next(item for item in payload["cases"] if item["case_id"] == "bad_new_claim_after_freeze_001")
    assert case["verdict"] == "fail"
    assert "claim_not_in_registry" in case["issues"]


def test_generic_candidate_action_warns() -> None:
    payload = load_json(ARTIFACTS / "failed_cases_result.json")
    case = next(item for item in payload["cases"] if item["case_id"] == "bad_generic_actions_001")
    assert case["verdict"] == "warn"
    assert "generic_action" in case["issues"]


def test_confirmed_action_without_evidence_fails() -> None:
    payload = load_json(ARTIFACTS / "failed_cases_result.json")
    case = next(item for item in payload["cases"] if item["case_id"] == "bad_confirmed_action_without_evidence_001")
    assert case["verdict"] == "fail"
    assert "confirmed_action_without_evidence" in case["issues"]


def test_fake_owner_due_status_fails() -> None:
    payload = load_json(ARTIFACTS / "failed_cases_result.json")
    case = next(item for item in payload["cases"] if item["case_id"] == "bad_fake_owner_due_status_001")
    assert case["verdict"] == "fail"
    assert {"fake_owner", "fake_due_date", "fake_status"}.issubset(set(case["issues"]))


def test_failed_case_writes_diagnostics_but_no_release_artifact() -> None:
    assert (ARTIFACTS / "golden_memo_pack_run_result.json").exists()
    assert (ARTIFACTS / "failed_cases_result.json").exists()
    assert (ARTIFACTS / "release_guard_result.json").exists()
    assert not (ARTIFACTS / "release_manifest.json").exists()
    assert not (ARTIFACTS / "accepted_memo.md").exists()
    assert load_json(ARTIFACTS / "release_guard_result.json")["status"] == "pass"


def test_judge_report_schema_is_real_json_schema() -> None:
    schema = load_json(ROOT / "schemas/judge_report.schema.json")
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["type"] == "object"
    assert set(["memo_id", "case_id", "verdict", "issues", "recommendation"]).issubset(schema["required"])


def test_release_manifest_schema_is_real_json_schema() -> None:
    schema = load_json(ROOT / "schemas/release_manifest.schema.json")
    assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"
    assert schema["type"] == "object"
    assert "release_status" in schema["required"]


def test_judge_report_schema_validates_sample_report() -> None:
    schema = load_json(ROOT / "schemas/judge_report.schema.json")
    sample = {
        "memo_id": "memo",
        "case_id": "case",
        "verdict": "fail",
        "issues": ["unsupported_claim"],
        "recommendation": "stop",
        "unsupported_claims": ["claim"],
        "formula_violations": [],
        "new_claims_after_freeze": [],
        "action_maturity_violations": []
    }
    jsonschema.validate(sample, schema)


def test_release_manifest_schema_validates_sample_manifest() -> None:
    schema = load_json(ROOT / "schemas/release_manifest.schema.json")
    sample = {
        "memo_id": "memo",
        "case_id": "case",
        "release_status": "blocked",
        "source_artifacts": ["a"],
        "judge_report_path": "judge.json",
        "created_at": "2026-05-23T00:00:00Z",
        "release_artifacts": [],
        "residual_risks": ["not production ready"]
    }
    jsonschema.validate(sample, schema)


def test_acceptance_checklist_status_values() -> None:
    text = (PACK / "acceptance_checklist.md").read_text(encoding="utf-8")
    assert "production_ready" in text or "acceptance" in text.lower()


def test_no_production_ready_claim() -> None:
    manifest = (PACK / "MANIFEST.md").read_text(encoding="utf-8")
    result = load_json(ARTIFACTS / "golden_memo_pack_run_result.json")
    assert "status: active_candidate" in manifest
    assert "production_ready: false" in manifest
    assert result["production_ready"] is False
