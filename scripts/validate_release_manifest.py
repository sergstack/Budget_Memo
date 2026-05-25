from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

import jsonschema


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = PROJECT_ROOT / "schemas/release_manifest.schema.json"


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_path(raw: str) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else PROJECT_ROOT / path


def validate_manifest(manifest_path: Path, schema_path: Path = DEFAULT_SCHEMA, high_risk: bool = False) -> dict[str, Any]:
    schema = load_json(schema_path)
    manifest = load_json(manifest_path)
    jsonschema.validate(manifest, schema)
    blockers = []
    if manifest.get("release_status") == "pass":
        required_gate_status = manifest.get("required_gates_status", "pass")
        if required_gate_status != "pass":
            blockers.append("release_status_pass_with_failed_required_gates")
    judge_path = resolve_path(str(manifest.get("judge_report_path", "")))
    if not judge_path.exists():
        blockers.append("judge_report_path_missing")
    render_path = manifest.get("render_qa_path")
    if render_path and not resolve_path(str(render_path)).exists():
        blockers.append("render_qa_path_missing")
    if manifest.get("render_required", False) and not render_path:
        blockers.append("render_qa_path_required")
    human_note = manifest.get("human_acceptance_note_path")
    if high_risk and not human_note:
        blockers.append("human_acceptance_note_required_for_high_risk")
    if high_risk and human_note and not resolve_path(str(human_note)).exists():
        blockers.append("human_acceptance_note_path_missing")
    status = "fail" if blockers else "pass"
    return {"status": status, "manifest": str(manifest_path), "blockers": blockers}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate release manifest against schema and doctrine release rules.")
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--schema", default=DEFAULT_SCHEMA, type=Path)
    parser.add_argument("--high-risk", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()
    result = validate_manifest(args.manifest, args.schema, args.high_risk)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
