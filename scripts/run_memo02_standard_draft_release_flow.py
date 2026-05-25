#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.diagnose_docx_visual_quality import diagnose_docx_visual_quality
from scripts.run_monthly_plan_fact_standard_draft_release_pilot import (
    DEFAULT_PERIOD,
    DEPTH_MODE,
    MEMO_ID,
    MEMO_PROFILE,
    Memo02DraftSourcePaths,
    _cli_source_paths,
    _detect_period,
    _missing_sources,
    _read_sources,
    build_memo02_standard_draft_contract,
    default_source_paths,
)
from src.memo_display_contract import contract_to_dict, validate_display_contract
from src.memo_release_manifest import (
    MemoReleaseManifest,
    ReleaseArtifactPaths,
    ReleaseDecision,
    ReleaseQaStatus,
    derive_release_status,
    manifest_to_dict,
    write_release_manifest,
)
from src.memo_renderer import render_memo_contract_to_docx


DRAFT_FLOW_ROOT = PROJECT_ROOT / "artifacts" / "draft_flows" / "memo02_standard"
DRAFT_DOCX_NAME = "monthly_plan_fact_memo__standard__draft.docx"


def default_output_dir(now: datetime | None = None) -> Path:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d_%H%M%SZ")
    return DRAFT_FLOW_ROOT / timestamp


def run_memo02_standard_draft_release_flow(
    out_dir: Path | None = None,
    source_paths: Memo02DraftSourcePaths | None = None,
    soffice_bin: str | None = None,
    now: datetime | None = None,
) -> dict:
    source_paths = source_paths or default_source_paths()
    output_dir = Path(out_dir) if out_dir is not None else default_output_dir(now)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract_path = output_dir / "memo_display_contract.json"
    docx_path = output_dir / DRAFT_DOCX_NAME
    visual_qa_dir = output_dir / "visual_qa"
    manifest_path = output_dir / "release_manifest.json"

    missing_sources = _missing_sources(source_paths)
    if missing_sources:
        manifest = _blocked_manifest(
            docx_path=docx_path,
            visual_qa_path=visual_qa_dir / "defects.json",
            manifest_path=manifest_path,
            blockers=[f"missing_source:{name}" for name in missing_sources],
            notes="Не найдены обязательные исходные файлы стандартной записки План-Факт; черновой поток остановлен.",
        )
        write_release_manifest(manifest, manifest_path)
        return _result("blocked", output_dir, contract_path, docx_path, visual_qa_dir, manifest_path, manifest, missing_sources)

    source_text = _read_sources(source_paths)
    period = _detect_period(source_text["readme"])
    contract = build_memo02_standard_draft_contract(source_text, period)
    contract_errors = validate_display_contract(contract)
    if contract_errors:
        manifest = _blocked_manifest(
            docx_path=docx_path,
            visual_qa_path=visual_qa_dir / "defects.json",
            manifest_path=manifest_path,
            blockers=[f"contract_validation:{error}" for error in contract_errors],
            notes="Проверка контракта отображения завершилась ошибкой; черновой поток остановлен.",
        )
        write_release_manifest(manifest, manifest_path)
        return _result("blocked", output_dir, contract_path, docx_path, visual_qa_dir, manifest_path, manifest, [])

    contract_path.write_text(json.dumps(contract_to_dict(contract), ensure_ascii=False, indent=2), encoding="utf-8")
    render_memo_contract_to_docx(contract, docx_path)
    visual_qa = diagnose_docx_visual_quality(docx_path, visual_qa_dir, soffice_bin=soffice_bin)

    content_qa_status = "pass"
    visual_qa_status = visual_qa["verdicts"]["overall_visual_release_status"]
    release_blockers = [blocker["id"] for blocker in visual_qa.get("release_blockers", [])]
    release_status = derive_release_status(content_qa_status, visual_qa_status, release_blockers)

    manifest = MemoReleaseManifest(
        memo_id=contract.memo_id,
        memo_profile=contract.memo_profile,
        depth_mode=contract.depth_mode,
        period=contract.period,
        created_at=datetime.now(timezone.utc).isoformat(),
        artifact_paths=ReleaseArtifactPaths(
            docx_path=str(docx_path),
            visual_qa_path=str(visual_qa_dir / "defects.json"),
            release_manifest_path=str(manifest_path),
        ),
        qa_status=ReleaseQaStatus(
            content_qa_status=content_qa_status,
            visual_qa_status=visual_qa_status,
            overall_visual_release_status=visual_qa["verdicts"]["overall_visual_release_status"],
        ),
        decision=ReleaseDecision(
            release_status=release_status,
            release_blockers=release_blockers,
            accepted_by="memo02-standard-draft-flow" if release_status == "pass" else "",
            rollback="Удалить выходной каталог чернового потока.",
        ),
        notes="Черновой поток стандартной записки План-Факт; финальное продвижение требует отдельного ручного разрешения.",
    )
    write_release_manifest(manifest, manifest_path)
    return _result(release_status, output_dir, contract_path, docx_path, visual_qa_dir, manifest_path, manifest, [])


def _blocked_manifest(
    docx_path: Path,
    visual_qa_path: Path,
    manifest_path: Path,
    blockers: list[str],
    notes: str,
) -> MemoReleaseManifest:
    return MemoReleaseManifest(
        memo_id=MEMO_ID,
        memo_profile=MEMO_PROFILE,
        depth_mode=DEPTH_MODE,
        period=DEFAULT_PERIOD,
        created_at=datetime.now(timezone.utc).isoformat(),
        artifact_paths=ReleaseArtifactPaths(
            docx_path=str(docx_path),
            visual_qa_path=str(visual_qa_path),
            release_manifest_path=str(manifest_path),
        ),
        qa_status=ReleaseQaStatus(
            content_qa_status="blocked",
            visual_qa_status="blocked",
            overall_visual_release_status="blocked",
        ),
        decision=ReleaseDecision(
            release_status="blocked",
            release_blockers=blockers,
            rollback="Удалить выходной каталог чернового потока.",
        ),
        notes=notes,
    )


def _result(
    status: str,
    output_dir: Path,
    contract_path: Path,
    docx_path: Path,
    visual_qa_dir: Path,
    manifest_path: Path,
    manifest: MemoReleaseManifest,
    missing_sources: list[str],
) -> dict:
    return {
        "status": status,
        "missing_sources": missing_sources,
        "output_dir": str(output_dir),
        "contract_path": str(contract_path),
        "docx_path": str(docx_path),
        "visual_qa_path": str(visual_qa_dir / "defects.json"),
        "release_manifest_path": str(manifest_path),
        "release_manifest": manifest_to_dict(manifest),
        "manual_approval_required": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run memo02 standard draft release flow. Final promotion is not performed.")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--soffice-bin", default=None)
    parser.add_argument("--readme", type=Path, default=None)
    parser.add_argument("--package-qa", type=Path, default=None)
    parser.add_argument("--evidence-map", type=Path, default=None)
    parser.add_argument("--chart-metadata", type=Path, default=None)
    args = parser.parse_args()

    source_paths = _cli_source_paths(args)
    result = run_memo02_standard_draft_release_flow(args.out, source_paths, soffice_bin=args.soffice_bin)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
