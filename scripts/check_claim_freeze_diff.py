from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def by_claim_id(items: Any) -> dict[str, dict[str, Any]]:
    if isinstance(items, dict):
        items = items.get("claims", [])
    return {str(item["claim_id"]): dict(item) for item in items}


def check_claim_freeze(frozen_path: Path, revised_path: Path) -> dict[str, Any]:
    frozen = by_claim_id(load_json(frozen_path))
    revised = by_claim_id(load_json(revised_path))
    new_claims = sorted(claim_id for claim_id in revised if claim_id not in frozen)
    changed_amounts = []
    changed_periods = []
    changed_formulas = []
    upgraded_claim_strength = []
    fake_evidence_ids = []
    known_evidence = {
        str(value)
        for item in frozen.values()
        for value in ([item.get("evidence_id")] if item.get("evidence_id") else [])
    }

    strength_rank = {"weak": 1, "hypothesis": 1, "interpretation": 2, "strong": 3, "fact": 3}
    for claim_id, revised_claim in revised.items():
        if claim_id not in frozen:
            continue
        frozen_claim = frozen[claim_id]
        if str(revised_claim.get("amount", "")) != str(frozen_claim.get("amount", "")):
            changed_amounts.append(claim_id)
        if str(revised_claim.get("period", "")) != str(frozen_claim.get("period", "")):
            changed_periods.append(claim_id)
        if str(revised_claim.get("formula", "")) != str(frozen_claim.get("formula", "")):
            changed_formulas.append(claim_id)
        old_strength = strength_rank.get(str(frozen_claim.get("strength", "")).lower(), 0)
        new_strength = strength_rank.get(str(revised_claim.get("strength", "")).lower(), 0)
        if new_strength > old_strength:
            upgraded_claim_strength.append(claim_id)
        evidence_id = revised_claim.get("evidence_id")
        if evidence_id and str(evidence_id) not in known_evidence:
            fake_evidence_ids.append(claim_id)

    failures = [
        new_claims,
        changed_amounts,
        changed_periods,
        changed_formulas,
        upgraded_claim_strength,
        fake_evidence_ids,
    ]
    return {
        "status": "fail" if any(failures) else "pass",
        "new_claims": new_claims,
        "changed_amounts": changed_amounts,
        "changed_periods": changed_periods,
        "changed_formulas": changed_formulas,
        "upgraded_claim_strength": upgraded_claim_strength,
        "fake_evidence_ids": fake_evidence_ids,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Check frozen claim registry against revised memo claims.")
    parser.add_argument("--frozen", required=True, type=Path)
    parser.add_argument("--revised", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    result = check_claim_freeze(args.frozen, args.revised)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
