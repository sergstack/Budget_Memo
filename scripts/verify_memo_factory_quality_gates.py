from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import yaml


REQUIRED_GATES = {
    "intake_scope",
    "data_contract",
    "mart_metric_verification",
    "evidence_claim_registry",
    "analyst_lenses",
    "narrative_writing",
    "judge_revision",
    "artifact_release_learning",
}

REQUIRED_STOP_RULES = {
    "data_contract_fail",
    "mart_verification_fail",
    "critical_claim_without_evidence",
    "formula_or_metric_fail",
    "evidence_judge_fail",
    "docx_render_qa_fail",
    "release_reviewer_fail",
}

REQUIRED_CLAIM_FREEZE_FORBIDDEN = {
    "add_new_claim",
    "add_new_reason",
    "change_amount",
    "change_period",
    "change_formula",
    "upgrade_weak_claim_to_strong",
    "invent_evidence",
}


def load_yaml(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def validate_gate_result(path: Path, known_gates: set[str]) -> list[str]:
    data = json.loads(path.read_text(encoding="utf-8"))
    blockers = []
    if data.get("gate") not in known_gates:
        blockers.append("gate_not_in_config")
    if data.get("status") not in {"pass", "warn", "fail", "blocked"}:
        blockers.append("invalid_gate_status")
    for key in ["memo_id", "checked_at", "blockers", "warnings", "artifacts"]:
        if key not in data:
            blockers.append(f"missing_{key}")
    return blockers


def verify_config(config: Path, gate_result: Path | None = None) -> dict[str, Any]:
    data = load_yaml(config)
    gate_ids = {str(item.get("id")) for item in data.get("gates", [])}
    stop_rules = {str(item) for item in data.get("stop_rules", [])}
    claim_freeze = data.get("claim_freeze", {}) or {}
    forbidden = {str(item) for item in claim_freeze.get("forbidden", [])}
    blockers = []
    missing_gates = sorted(REQUIRED_GATES - gate_ids)
    missing_stop_rules = sorted(REQUIRED_STOP_RULES - stop_rules)
    missing_forbidden = sorted(REQUIRED_CLAIM_FREEZE_FORBIDDEN - forbidden)
    if missing_gates:
        blockers.append(f"missing_gates:{','.join(missing_gates)}")
    if missing_stop_rules:
        blockers.append(f"missing_stop_rules:{','.join(missing_stop_rules)}")
    if claim_freeze.get("after_gate") != "evidence_claim_registry":
        blockers.append("claim_freeze_after_gate_invalid")
    if missing_forbidden:
        blockers.append(f"missing_claim_freeze_forbidden:{','.join(missing_forbidden)}")
    if gate_result:
        blockers.extend(validate_gate_result(gate_result, gate_ids))
    return {
        "status": "fail" if blockers else "pass",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "config": str(config),
        "gates": sorted(gate_ids),
        "stop_rules": sorted(stop_rules),
        "claim_freeze_after_gate": claim_freeze.get("after_gate"),
        "blockers": blockers,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify memo factory quality gate doctrine config.")
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--gate-result", type=Path)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = verify_config(args.config, args.gate_result)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
