from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema
import yaml


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests/fixtures/memo_factory_doctrine"


def run_cmd(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=False)


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def test_quality_gates_config_exists_and_contains_8_gates() -> None:
    data = yaml.safe_load((ROOT / "config/memo_factory_quality_gates.yml").read_text(encoding="utf-8"))
    assert len(data["gates"]) == 8
    assert {item["id"] for item in data["gates"]} == {
        "intake_scope",
        "data_contract",
        "mart_metric_verification",
        "evidence_claim_registry",
        "analyst_lenses",
        "narrative_writing",
        "judge_revision",
        "artifact_release_learning",
    }


def test_stop_rules_exist() -> None:
    data = yaml.safe_load((ROOT / "config/memo_factory_quality_gates.yml").read_text(encoding="utf-8"))
    assert "release_reviewer_fail" in data["stop_rules"]
    assert "critical_claim_without_evidence" in data["stop_rules"]


def test_claim_freeze_forbidden_rules_exist() -> None:
    data = yaml.safe_load((ROOT / "config/memo_factory_quality_gates.yml").read_text(encoding="utf-8"))
    forbidden = set(data["claim_freeze"]["forbidden"])
    assert {"add_new_claim", "change_amount", "change_period", "change_formula", "invent_evidence"}.issubset(forbidden)


def test_routing_config_exists_and_contains_required_roles() -> None:
    data = load_json(ROOT / "config/memo_factory_routing_config.json")
    roles = set(data["roles"])
    assert {
        "writer",
        "json_schema_builder",
        "revisor",
        "finance_checker",
        "evidence_judge",
        "logic_judge",
        "russian_editor",
        "summarizer",
        "release_reviewer",
        "final_fallback",
    }.issubset(roles)
    assert data["roles"]["writer"]["primary_model"] == "qwen2.5-coder:32b"
    assert data["roles"]["evidence_judge"]["fallback_model"] == "mistral-small:latest"


def test_routing_config_includes_fallback_metadata_requirements() -> None:
    data = load_json(ROOT / "config/memo_factory_routing_config.json")
    required = set(data["metadata_requirements"])
    for role in data["roles"].values():
        assert required.issubset(role)


def test_quality_gate_verifier_passes_valid_config() -> None:
    result = run_cmd([sys.executable, "scripts/verify_memo_factory_quality_gates.py", "--config", "config/memo_factory_quality_gates.yml"])
    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["status"] == "pass"


def test_quality_gate_verifier_fails_missing_stop_rule_fixture() -> None:
    result = run_cmd([sys.executable, "scripts/verify_memo_factory_quality_gates.py", "--config", str(FIXTURES / "quality_gates_missing_stop_rule.yml")])
    assert result.returncode == 1
    assert "missing_stop_rules" in result.stdout


def test_release_manifest_schema_validates_valid_sample() -> None:
    schema = load_json(ROOT / "schemas/release_manifest.schema.json")
    jsonschema.validate(load_json(FIXTURES / "release_manifest_valid.json"), schema)


def test_release_manifest_schema_rejects_missing_required_fields() -> None:
    schema = load_json(ROOT / "schemas/release_manifest.schema.json")
    try:
        jsonschema.validate(load_json(FIXTURES / "release_manifest_missing_required.json"), schema)
    except jsonschema.ValidationError:
        return
    raise AssertionError("schema accepted invalid manifest")


def test_high_risk_release_readiness_blocks_when_human_review_is_missing(tmp_path: Path) -> None:
    result = run_cmd([
        sys.executable,
        "scripts/verify_high_risk_release_readiness.py",
        "--input",
        str(FIXTURES / "high_risk_missing_human_review.json"),
        "--out-json",
        str(tmp_path / "readiness.json"),
        "--out-md",
        str(tmp_path / "readiness.md"),
    ])
    assert result.returncode == 1
    payload = load_json(tmp_path / "readiness.json")
    assert payload["status"] == "blocked"
    assert "human_review_required_or_pending" in payload["blockers"]


def test_claim_freeze_release_verifier_fails_on_new_claim_after_freeze(tmp_path: Path) -> None:
    result = run_cmd([
        sys.executable,
        "scripts/verify_claim_freeze_for_release.py",
        "--frozen",
        "tests/fixtures/golden_memo_pack/frozen_claim_registry.json",
        "--revised",
        "tests/fixtures/golden_memo_pack/revised_claims.json",
        "--out",
        str(tmp_path / "claim_freeze.json"),
    ])
    assert result.returncode == 1
    payload = load_json(tmp_path / "claim_freeze.json")
    assert payload["status"] == "fail"
    assert payload["release_allowed"] is False
    assert payload["new_claims"]


def test_no_production_memo_outputs_are_used_as_mutable_fixtures() -> None:
    fixture_paths = [str(path) for path in FIXTURES.rglob("*") if path.is_file()]
    assert not any("06_reports/" in path for path in fixture_paths)
    assert not any("02_stage/" in path or "03_marts/" in path for path in fixture_paths)
