from __future__ import annotations

import json
from pathlib import Path

import pytest
from docx import Document

from scripts import publish_memo02_standard_final_release as gate
from scripts.publish_memo02_standard_final_release import publish_memo02_standard_final_release
from src.memo_release_manifest import (
    MemoReleaseManifest,
    ReleaseArtifactPaths,
    ReleaseDecision,
    ReleaseQaStatus,
    write_release_manifest,
)


def test_publishes_approved_package_to_approved_period_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(gate, "REPORT_ROOT", tmp_path / "06_reports" / "02_monthly_plan_fact_memo")
    monkeypatch.setattr(gate, "APPROVED_DRAFT_ROOT", tmp_path / "artifacts" / "approved_drafts" / "memo02_standard")
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "20260525_191106Z")

    result = publish_memo02_standard_final_release(approved_dir, "Publisher")

    target_dir = gate.REPORT_ROOT / "approved" / "2026-04"
    assert result["status"] == "published"
    assert Path(result["published_dir"]) == target_dir.resolve()
    assert (target_dir / "monthly_plan_fact_memo__standard__draft.docx").exists()
    assert (target_dir / "release_manifest.json").exists()
    assert (target_dir / "approval_record.json").exists()
    publication = json.loads((target_dir / "publication_record.json").read_text(encoding="utf-8"))
    assert publication["published_by"] == "Publisher"
    assert publication["target"] == "approved"
    assert publication["production_pipeline_run"] is False
    assert publication["ollama_run"] is False


def test_requires_published_by(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run")

    with pytest.raises(ValueError, match="--published-by is required"):
        publish_memo02_standard_final_release(approved_dir, "")


def test_rejects_missing_approval_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run")
    (approved_dir / "approval_record.json").unlink()

    with pytest.raises(FileNotFoundError, match="missing approval record"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_rejects_empty_approved_by(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run", approved_by="")

    with pytest.raises(ValueError, match="approval_record.approved_by"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_rejects_already_final_promoted_record(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run", final_promotion_performed=True)

    with pytest.raises(ValueError, match="final_promotion_performed must be false"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_rejects_non_pass_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run", release_status="blocked")

    with pytest.raises(ValueError, match="release_status must be pass"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_rejects_non_pass_visual_qa(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run", visual_qa_status="blocked")

    with pytest.raises(ValueError, match="invalid release manifest"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_rejects_release_blockers(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run")
    data = json.loads((approved_dir / "release_manifest.json").read_text(encoding="utf-8"))
    data["decision"]["release_blockers"] = ["VQA-001"]
    (approved_dir / "release_manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    with pytest.raises(ValueError, match="invalid release manifest"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_rejects_missing_docx(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run")
    (approved_dir / "monthly_plan_fact_memo__standard__draft.docx").unlink()

    with pytest.raises(FileNotFoundError, match="missing approved DOCX"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_refuses_overwrite_without_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run")

    publish_memo02_standard_final_release(approved_dir, "Publisher")

    with pytest.raises(FileExistsError, match="publication output already exists"):
        publish_memo02_standard_final_release(approved_dir, "Publisher")


def test_allows_explicit_final_target_under_final_period_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run")

    result = publish_memo02_standard_final_release(approved_dir, "Publisher", target="final")

    target_dir = gate.REPORT_ROOT / "final" / "2026-04"
    assert Path(result["published_dir"]) == target_dir.resolve()
    assert (target_dir / "publication_record.json").exists()


def test_writes_only_publication_output_folder(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    configure_roots(tmp_path, monkeypatch)
    approved_dir = write_approved_dir(gate.APPROVED_DRAFT_ROOT / "run")
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    publish_memo02_standard_final_release(approved_dir, "Publisher")

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    created = [path for path in after if path not in before]
    assert created
    allowed = Path("06_reports/02_monthly_plan_fact_memo/approved/2026-04")
    assert all(path == allowed or path in allowed.parents or path.is_relative_to(allowed) for path in created)


def configure_roots(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(gate, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(gate, "REPORT_ROOT", tmp_path / "06_reports" / "02_monthly_plan_fact_memo")
    monkeypatch.setattr(gate, "APPROVED_DRAFT_ROOT", tmp_path / "artifacts" / "approved_drafts" / "memo02_standard")


def write_approved_dir(
    approved_dir: Path,
    approved_by: str = "Reviewer",
    final_promotion_performed: bool = False,
    release_status: str = "pass",
    visual_qa_status: str = "pass",
) -> Path:
    approved_dir.mkdir(parents=True, exist_ok=True)
    docx_path = approved_dir / "monthly_plan_fact_memo__standard__draft.docx"
    document = Document()
    document.add_paragraph("Утвержденный черновой документ Word")
    document.save(docx_path)
    manifest = MemoReleaseManifest(
        memo_id="monthly_plan_fact_memo__standard__draft",
        memo_profile="monthly_plan_fact_memo",
        depth_mode="standard",
        period="2026-04",
        created_at="2026-05-25T00:00:00Z",
        artifact_paths=ReleaseArtifactPaths(
            docx_path=str(docx_path),
            visual_qa_path=str(approved_dir / "visual_qa" / "defects.json"),
            release_manifest_path=str(approved_dir / "release_manifest.json"),
        ),
        qa_status=ReleaseQaStatus(
            content_qa_status="pass",
            visual_qa_status=visual_qa_status,
            overall_visual_release_status=visual_qa_status,
        ),
        decision=ReleaseDecision(
            release_status=release_status,
            release_blockers=[],
            accepted_by="draft-flow" if release_status == "pass" else "",
            rollback="Удалить выходной каталог чернового потока.",
        ),
    )
    if release_status == "pass" and visual_qa_status == "pass":
        write_release_manifest(manifest, approved_dir / "release_manifest.json")
    else:
        data = {
            "memo_id": manifest.memo_id,
            "memo_profile": manifest.memo_profile,
            "depth_mode": manifest.depth_mode,
            "period": manifest.period,
            "created_at": manifest.created_at,
            "artifact_paths": {
                "docx_path": str(docx_path),
                "visual_qa_path": str(approved_dir / "visual_qa" / "defects.json"),
                "release_manifest_path": str(approved_dir / "release_manifest.json"),
            },
            "qa_status": {
                "content_qa_status": "pass",
                "visual_qa_status": visual_qa_status,
                "overall_visual_release_status": visual_qa_status,
            },
            "decision": {
                "release_status": release_status,
                "release_blockers": [],
                "accepted_by": "draft-flow" if release_status == "pass" else "",
                "rollback": "Удалить выходной каталог чернового потока.",
            },
        }
        (approved_dir / "release_manifest.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    approval_record = {
        "approved_by": approved_by,
        "approved_at": "2026-05-25T00:00:00Z",
        "approved_docx_path": str(docx_path),
        "approved_manifest_path": str(approved_dir / "release_manifest.json"),
        "final_promotion_performed": final_promotion_performed,
    }
    (approved_dir / "approval_record.json").write_text(json.dumps(approval_record, ensure_ascii=False, indent=2), encoding="utf-8")
    return approved_dir
