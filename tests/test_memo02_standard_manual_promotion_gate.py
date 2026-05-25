from __future__ import annotations

import json
from pathlib import Path

import pytest
from docx import Document

from scripts.promote_memo02_standard_draft_release import promote_memo02_standard_draft_release
from src.memo_release_manifest import (
    MemoReleaseManifest,
    ReleaseArtifactPaths,
    ReleaseDecision,
    ReleaseQaStatus,
    write_release_manifest,
)


def test_promotes_passed_draft_to_approved_output_only(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")
    approved_dir = tmp_path / "approved"

    result = promote_memo02_standard_draft_release(draft_dir, "Finance reviewer", approved_dir)

    assert result["status"] == "promoted_to_approved_draft"
    assert result["final_promotion_performed"] is False
    assert (approved_dir / "monthly_plan_fact_memo__standard__draft.docx").exists()
    assert (approved_dir / "release_manifest.json").exists()
    record = json.loads((approved_dir / "approval_record.json").read_text(encoding="utf-8"))
    assert record["approved_by"] == "Finance reviewer"
    assert record["manual_approval_gate"] is True
    assert record["final_promotion_performed"] is False


def test_requires_approved_by(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")

    with pytest.raises(ValueError, match="--approved-by is required"):
        promote_memo02_standard_draft_release(draft_dir, "", tmp_path / "approved")


def test_rejects_non_pass_release_status(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft", release_status="blocked")

    with pytest.raises(ValueError, match="release_status must be pass"):
        promote_memo02_standard_draft_release(draft_dir, "Reviewer", tmp_path / "approved")


def test_rejects_release_blockers(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")
    data = json.loads((draft_dir / "release_manifest.json").read_text(encoding="utf-8"))
    data["decision"]["release_blockers"] = ["VQA-001"]
    (draft_dir / "release_manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid release manifest"):
        promote_memo02_standard_draft_release(draft_dir, "Reviewer", tmp_path / "approved")


def test_refuses_overwrite_without_explicit_flag(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")
    approved_dir = tmp_path / "approved"

    promote_memo02_standard_draft_release(draft_dir, "Reviewer", approved_dir)

    with pytest.raises(FileExistsError, match="approved output already exists"):
        promote_memo02_standard_draft_release(draft_dir, "Reviewer", approved_dir)


def test_overwrite_requires_explicit_flag(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")
    approved_dir = tmp_path / "approved"

    promote_memo02_standard_draft_release(draft_dir, "Reviewer", approved_dir)
    result = promote_memo02_standard_draft_release(draft_dir, "Reviewer", approved_dir, overwrite=True)

    assert result["status"] == "promoted_to_approved_draft"


def test_rejects_forbidden_output_layer(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")

    with pytest.raises(ValueError, match="forbidden project layer"):
        promote_memo02_standard_draft_release(draft_dir, "Reviewer", Path("06_reports") / "memo02")


def test_missing_docx_blocks_promotion(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")
    (draft_dir / "monthly_plan_fact_memo__standard__draft.docx").unlink()

    with pytest.raises(FileNotFoundError, match="missing draft DOCX"):
        promote_memo02_standard_draft_release(draft_dir, "Reviewer", tmp_path / "approved")


def test_writes_only_approved_output_dir(tmp_path: Path) -> None:
    draft_dir = write_draft_dir(tmp_path / "draft")
    approved_dir = tmp_path / "approved"
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    promote_memo02_standard_draft_release(draft_dir, "Reviewer", approved_dir)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    created = [path for path in after if path not in before]
    assert created
    assert all(path == Path("approved") or path.is_relative_to(Path("approved")) for path in created)


def write_draft_dir(
    draft_dir: Path,
    release_status: str = "pass",
    release_blockers: list[str] | None = None,
) -> Path:
    draft_dir.mkdir(parents=True, exist_ok=True)
    docx_path = draft_dir / "monthly_plan_fact_memo__standard__draft.docx"
    document = Document()
    document.add_paragraph("Черновой документ Word")
    document.save(docx_path)
    release_blockers = release_blockers or []
    visual_status = "pass" if release_status == "pass" and not release_blockers else "blocked"
    manifest = MemoReleaseManifest(
        memo_id="monthly_plan_fact_memo__standard__draft",
        memo_profile="monthly_plan_fact_memo",
        depth_mode="standard",
        period="2026-04",
        created_at="2026-05-25T00:00:00Z",
        artifact_paths=ReleaseArtifactPaths(
            docx_path=str(docx_path),
            visual_qa_path=str(draft_dir / "visual_qa" / "defects.json"),
            release_manifest_path=str(draft_dir / "release_manifest.json"),
        ),
        qa_status=ReleaseQaStatus(
            content_qa_status="pass",
            visual_qa_status=visual_status,
            overall_visual_release_status=visual_status,
        ),
        decision=ReleaseDecision(
            release_status=release_status,
            release_blockers=release_blockers,
            accepted_by="draft-flow" if release_status == "pass" else "",
            rollback="Удалить выходной каталог чернового потока.",
        ),
    )
    write_release_manifest(manifest, draft_dir / "release_manifest.json")
    return draft_dir
