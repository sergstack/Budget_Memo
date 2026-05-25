from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.memo_release_manifest import (
    MemoReleaseManifest,
    ReleaseArtifactPaths,
    ReleaseDecision,
    ReleaseQaStatus,
    derive_release_status,
    manifest_from_dict,
    manifest_to_dict,
    validate_release_manifest,
    write_release_manifest,
)


def pass_manifest() -> MemoReleaseManifest:
    return MemoReleaseManifest(
        memo_id="memo_01",
        memo_profile="executive_yoy_mom_budget_memo",
        depth_mode="standard",
        period="2026-04",
        created_at="2026-05-25T00:00:00Z",
        artifact_paths=ReleaseArtifactPaths(
            docx_path="06_reports/memo/final/memo.docx",
            markdown_path="06_reports/memo/final/memo.md",
            content_qa_path="07_qa/content.json",
            visual_qa_path="artifacts/diagnostics/visual/defects.json",
        ),
        qa_status=ReleaseQaStatus(
            content_qa_status="pass",
            visual_qa_status="pass",
            overall_visual_release_status="pass",
        ),
        decision=ReleaseDecision(
            release_status="pass",
            release_blockers=[],
            accepted_by="Finance QA",
            rollback="Revert release manifest and keep prior accepted artifact.",
        ),
        source_commit="abc123",
        notes="synthetic test manifest",
    )


def test_pass_manifest_validates() -> None:
    assert validate_release_manifest(pass_manifest()) == []


def test_blocked_manifest_with_visual_blocker_validates() -> None:
    manifest = MemoReleaseManifest(
        memo_id="memo_01",
        memo_profile="executive_yoy_mom_budget_memo",
        depth_mode="standard",
        period="2026-04",
        created_at="2026-05-25T00:00:00Z",
        artifact_paths=ReleaseArtifactPaths(docx_path="06_reports/memo/final/memo.docx"),
        qa_status=ReleaseQaStatus(
            content_qa_status="pass",
            visual_qa_status="blocked",
            overall_visual_release_status="blocked",
        ),
        decision=ReleaseDecision(
            release_status="blocked",
            release_blockers=["VQA-001"],
            rollback="Keep prior accepted artifact.",
        ),
    )

    assert validate_release_manifest(manifest) == []


def test_pass_manifest_with_release_blockers_fails_validation() -> None:
    manifest = pass_manifest()
    manifest = MemoReleaseManifest(
        **{
            **manifest_to_dict(manifest),
            "artifact_paths": manifest.artifact_paths,
            "qa_status": manifest.qa_status,
            "decision": ReleaseDecision(
                release_status="pass",
                release_blockers=["VQA-001"],
                accepted_by="Finance QA",
                rollback="Rollback.",
            ),
        }
    )

    assert any("empty release_blockers" in error for error in validate_release_manifest(manifest))


def test_pass_manifest_with_visual_qa_status_blocked_fails_validation() -> None:
    manifest = pass_manifest()
    manifest = MemoReleaseManifest(
        **{
            **manifest_to_dict(manifest),
            "artifact_paths": manifest.artifact_paths,
            "qa_status": ReleaseQaStatus("pass", "blocked", "blocked"),
            "decision": manifest.decision,
        }
    )

    assert any("visual_qa_status pass" in error for error in validate_release_manifest(manifest))


def test_derive_release_status_returns_pass_revise_blocked() -> None:
    assert derive_release_status("pass", "pass", []) == "pass"
    assert derive_release_status("revise", "pass", []) == "revise"
    assert derive_release_status("pass", "revise", []) == "revise"
    assert derive_release_status("blocked", "pass", []) == "blocked"
    assert derive_release_status("pass", "fail", []) == "blocked"
    assert derive_release_status("pass", "pass", ["VQA-001"]) == "blocked"


def test_round_trip_to_from_dict_preserves_key_fields() -> None:
    manifest = pass_manifest()

    restored = manifest_from_dict(manifest_to_dict(manifest))

    assert restored == manifest
    assert restored.memo_id == "memo_01"
    assert restored.artifact_paths.docx_path.endswith("memo.docx")
    assert restored.decision.release_status == "pass"


def test_write_release_manifest_writes_only_output_path_in_tmp_path(tmp_path: Path) -> None:
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    output_path = tmp_path / "manifest" / "release_manifest.json"

    result = write_release_manifest(pass_manifest(), output_path)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    assert result == output_path
    assert json.loads(output_path.read_text(encoding="utf-8"))["memo_id"] == "memo_01"
    assert before == []
    assert after == [Path("manifest"), Path("manifest/release_manifest.json")]


def test_invalid_manifest_raises_value_error_before_write(tmp_path: Path) -> None:
    manifest = MemoReleaseManifest(
        memo_id="",
        memo_profile="",
        depth_mode="",
        period="",
        created_at="2026-05-25T00:00:00Z",
        artifact_paths=ReleaseArtifactPaths(docx_path=""),
        qa_status=ReleaseQaStatus("unknown", "pass", "pass"),
        decision=ReleaseDecision("pass", rollback=""),
    )
    output_path = tmp_path / "release_manifest.json"

    with pytest.raises(ValueError, match="Invalid MemoReleaseManifest"):
        write_release_manifest(manifest, output_path)

    assert not output_path.exists()
