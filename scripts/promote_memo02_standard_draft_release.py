#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.memo_release_manifest import manifest_from_dict, validate_release_manifest


APPROVED_ROOT = PROJECT_ROOT / "artifacts" / "approved_drafts" / "memo02_standard"
DOCX_NAME = "monthly_plan_fact_memo__standard__draft.docx"
MANIFEST_NAME = "release_manifest.json"
APPROVAL_RECORD_NAME = "approval_record.json"


def promote_memo02_standard_draft_release(
    draft_dir: Path,
    approved_by: str,
    out_dir: Path | None = None,
    overwrite: bool = False,
) -> dict:
    if not approved_by.strip():
        raise ValueError("--approved-by is required")

    draft_dir = Path(draft_dir).expanduser().resolve()
    manifest_path = draft_dir / MANIFEST_NAME
    if not manifest_path.is_file():
        raise FileNotFoundError(f"missing release manifest: {manifest_path}")

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = manifest_from_dict(manifest_data)
    errors = validate_release_manifest(manifest)
    if errors:
        raise ValueError("invalid release manifest: " + "; ".join(errors))
    if manifest.decision.release_status != "pass":
        raise ValueError(f"release_status must be pass, got {manifest.decision.release_status}")
    if manifest.decision.release_blockers:
        raise ValueError("release_blockers must be empty")

    docx_path = _resolve_artifact_path(manifest.artifact_paths.docx_path, draft_dir)
    if not docx_path.is_file():
        raise FileNotFoundError(f"missing draft DOCX: {docx_path}")

    target_dir = Path(out_dir).expanduser().resolve() if out_dir is not None else APPROVED_ROOT / draft_dir.name
    _assert_safe_output_dir(target_dir)
    if target_dir.exists() and any(target_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"approved output already exists: {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)

    approved_docx = target_dir / DOCX_NAME
    approved_manifest = target_dir / MANIFEST_NAME
    approval_record = target_dir / APPROVAL_RECORD_NAME
    for path in [approved_docx, approved_manifest, approval_record]:
        if path.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite existing file: {path}")

    shutil.copy2(docx_path, approved_docx)
    shutil.copy2(manifest_path, approved_manifest)

    record = {
        "approved_by": approved_by,
        "approved_at": datetime.now(timezone.utc).isoformat(),
        "source_draft_dir": str(draft_dir),
        "source_docx_path": str(docx_path),
        "source_manifest_path": str(manifest_path),
        "approved_docx_path": str(approved_docx),
        "approved_manifest_path": str(approved_manifest),
        "release_status": manifest.decision.release_status,
        "release_blockers": manifest.decision.release_blockers,
        "manual_approval_gate": True,
        "final_promotion_performed": False,
    }
    approval_record.write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "status": "promoted_to_approved_draft",
        "approved_by": approved_by,
        "approved_dir": str(target_dir),
        "approved_docx_path": str(approved_docx),
        "approved_manifest_path": str(approved_manifest),
        "approval_record_path": str(approval_record),
        "final_promotion_performed": False,
    }


def _resolve_artifact_path(value: str, draft_dir: Path) -> Path:
    path = Path(value).expanduser()
    if path.is_absolute():
        return path.resolve()
    candidate = (PROJECT_ROOT / path).resolve()
    if candidate.exists():
        return candidate
    return (draft_dir / path).resolve()


def _assert_safe_output_dir(path: Path) -> None:
    resolved = path.resolve()
    forbidden_roots = [
        PROJECT_ROOT / "01_raw",
        PROJECT_ROOT / "02_stage",
        PROJECT_ROOT / "03_marts",
        PROJECT_ROOT / "04_charts",
        PROJECT_ROOT / "04_signals",
        PROJECT_ROOT / "05_evidence",
        PROJECT_ROOT / "05_llm_package",
        PROJECT_ROOT / "06_reports",
        PROJECT_ROOT / "07_qa",
        PROJECT_ROOT / "99_archive",
    ]
    for root in forbidden_roots:
        root = root.resolve()
        if resolved == root or root in resolved.parents:
            raise ValueError(f"approved output cannot be under forbidden project layer: {root}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Manual approval gate for memo02 standard draft release outputs.")
    parser.add_argument("--draft-dir", required=True, type=Path)
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    result = promote_memo02_standard_draft_release(
        draft_dir=args.draft_dir,
        approved_by=args.approved_by,
        out_dir=args.out,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
