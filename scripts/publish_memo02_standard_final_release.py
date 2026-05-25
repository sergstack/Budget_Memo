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


REPORT_ROOT = PROJECT_ROOT / "06_reports" / "02_monthly_plan_fact_memo"
APPROVED_DRAFT_ROOT = PROJECT_ROOT / "artifacts" / "approved_drafts" / "memo02_standard"
DOCX_NAME = "monthly_plan_fact_memo__standard__draft.docx"
MANIFEST_NAME = "release_manifest.json"
APPROVAL_RECORD_NAME = "approval_record.json"
PUBLICATION_RECORD_NAME = "publication_record.json"


def publish_memo02_standard_final_release(
    approved_dir: Path,
    published_by: str,
    out_dir: Path | None = None,
    overwrite: bool = False,
) -> dict:
    if not published_by.strip():
        raise ValueError("--published-by is required")

    approved_dir = Path(approved_dir).expanduser().resolve()
    _assert_approved_source_dir(approved_dir)
    approval_record_path = approved_dir / APPROVAL_RECORD_NAME
    manifest_path = approved_dir / MANIFEST_NAME
    docx_path = approved_dir / DOCX_NAME

    approval_record = _read_json_file(approval_record_path, "approval record")
    if not str(approval_record.get("approved_by", "")).strip():
        raise ValueError("approval_record.approved_by is required")
    if approval_record.get("final_promotion_performed") is not False:
        raise ValueError("approval_record.final_promotion_performed must be false")

    manifest_data = _read_json_file(manifest_path, "release manifest")
    manifest = manifest_from_dict(manifest_data)
    errors = validate_release_manifest(manifest)
    if errors:
        raise ValueError("invalid release manifest: " + "; ".join(errors))
    if manifest.decision.release_status != "pass":
        raise ValueError(f"release_status must be pass, got {manifest.decision.release_status}")
    if manifest.qa_status.visual_qa_status != "pass":
        raise ValueError(f"visual_qa_status must be pass, got {manifest.qa_status.visual_qa_status}")
    if manifest.decision.release_blockers:
        raise ValueError("release_blockers must be empty")
    if not docx_path.is_file():
        raise FileNotFoundError(f"missing approved DOCX: {docx_path}")

    target_dir = Path(out_dir).expanduser().resolve() if out_dir is not None else REPORT_ROOT / "approved" / manifest.period
    _assert_publication_target_dir(target_dir)
    if target_dir.exists() and any(target_dir.iterdir()) and not overwrite:
        raise FileExistsError(f"publication output already exists: {target_dir}")
    target_dir.mkdir(parents=True, exist_ok=True)

    published_docx = target_dir / DOCX_NAME
    published_manifest = target_dir / MANIFEST_NAME
    published_approval_record = target_dir / APPROVAL_RECORD_NAME
    publication_record_path = target_dir / PUBLICATION_RECORD_NAME
    for path in [published_docx, published_manifest, published_approval_record, publication_record_path]:
        if path.exists() and not overwrite:
            raise FileExistsError(f"refusing to overwrite existing file: {path}")

    shutil.copy2(docx_path, published_docx)
    shutil.copy2(manifest_path, published_manifest)
    shutil.copy2(approval_record_path, published_approval_record)

    publication_record = {
        "published_by": published_by,
        "published_at": datetime.now(timezone.utc).isoformat(),
        "target": "approved",
        "source_approved_dir": str(approved_dir),
        "published_dir": str(target_dir),
        "published_docx_path": str(published_docx),
        "published_manifest_path": str(published_manifest),
        "published_approval_record_path": str(published_approval_record),
        "release_status": manifest.decision.release_status,
        "visual_qa_status": manifest.qa_status.visual_qa_status,
        "release_blockers": manifest.decision.release_blockers,
        "approved_by": approval_record["approved_by"],
        "raw_stage_mart_recalculation_performed": False,
        "production_pipeline_run": False,
        "ollama_run": False,
    }
    publication_record_path.write_text(json.dumps(publication_record, ensure_ascii=False, indent=2), encoding="utf-8")

    return {
        "status": "published",
        "target": "approved",
        "published_by": published_by,
        "published_dir": str(target_dir),
        "published_docx_path": str(published_docx),
        "published_manifest_path": str(published_manifest),
        "published_approval_record_path": str(published_approval_record),
        "publication_record_path": str(publication_record_path),
    }


def _read_json_file(path: Path, label: str) -> dict:
    if not path.is_file():
        raise FileNotFoundError(f"missing {label}: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def _assert_approved_source_dir(path: Path) -> None:
    root = APPROVED_DRAFT_ROOT.resolve()
    if path != root and root not in path.parents:
        raise ValueError(f"approved source must be under {root}")


def _assert_publication_target_dir(path: Path) -> None:
    expected_root = (REPORT_ROOT / "approved").resolve()
    resolved = path.resolve()
    if resolved != expected_root and expected_root not in resolved.parents:
        raise ValueError(f"publication output must be under {expected_root}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish approved memo02 standard draft package to approved report folder.")
    parser.add_argument("--approved-dir", required=True, type=Path)
    parser.add_argument("--published-by", required=True)
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--overwrite", action="store_true")
    args = parser.parse_args()

    result = publish_memo02_standard_final_release(
        approved_dir=args.approved_dir,
        published_by=args.published_by,
        out_dir=args.out,
        overwrite=args.overwrite,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
