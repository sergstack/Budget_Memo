from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


PASS = "pass"
REVISE = "revise"
BLOCKED = "blocked"
FAIL = "fail"

ALLOWED_QA_STATUSES = {PASS, REVISE, BLOCKED, FAIL}
ALLOWED_RELEASE_STATUSES = {PASS, REVISE, BLOCKED}


@dataclass(frozen=True)
class ReleaseArtifactPaths:
    docx_path: str
    markdown_path: str = ""
    content_qa_path: str = ""
    visual_qa_path: str = ""
    release_manifest_path: str = ""


@dataclass(frozen=True)
class ReleaseQaStatus:
    content_qa_status: str
    visual_qa_status: str
    overall_visual_release_status: str


@dataclass(frozen=True)
class ReleaseDecision:
    release_status: str
    release_blockers: list[str] = field(default_factory=list)
    accepted_by: str = ""
    rollback: str = ""


@dataclass(frozen=True)
class MemoReleaseManifest:
    memo_id: str
    memo_profile: str
    depth_mode: str
    period: str
    created_at: str
    artifact_paths: ReleaseArtifactPaths
    qa_status: ReleaseQaStatus
    decision: ReleaseDecision
    source_commit: str = ""
    notes: str = ""


def derive_release_status(content_qa_status: str, visual_qa_status: str, release_blockers: list[str]) -> str:
    if release_blockers:
        return BLOCKED
    if content_qa_status in {BLOCKED, FAIL}:
        return BLOCKED
    if visual_qa_status in {BLOCKED, FAIL}:
        return BLOCKED
    if content_qa_status == REVISE or visual_qa_status == REVISE:
        return REVISE
    if content_qa_status == PASS and visual_qa_status == PASS:
        return PASS
    return BLOCKED


def validate_release_manifest(manifest: MemoReleaseManifest) -> list[str]:
    errors: list[str] = []
    if not manifest.memo_id.strip():
        errors.append("missing memo_id")
    if not manifest.memo_profile.strip():
        errors.append("missing memo_profile")
    if not manifest.depth_mode.strip():
        errors.append("missing depth_mode")
    if not manifest.period.strip():
        errors.append("missing period")
    if not manifest.artifact_paths.docx_path.strip():
        errors.append("missing docx_path")
    if manifest.qa_status.content_qa_status not in ALLOWED_QA_STATUSES:
        errors.append(f"invalid content_qa_status: {manifest.qa_status.content_qa_status}")
    if manifest.qa_status.visual_qa_status not in ALLOWED_QA_STATUSES:
        errors.append(f"invalid visual_qa_status: {manifest.qa_status.visual_qa_status}")
    if manifest.qa_status.overall_visual_release_status not in ALLOWED_RELEASE_STATUSES:
        errors.append(f"invalid overall_visual_release_status: {manifest.qa_status.overall_visual_release_status}")
    if manifest.decision.release_status not in ALLOWED_RELEASE_STATUSES:
        errors.append(f"invalid release_status: {manifest.decision.release_status}")
    if not manifest.decision.rollback.strip():
        errors.append("missing rollback")

    if manifest.decision.release_status == PASS:
        if manifest.qa_status.content_qa_status != PASS:
            errors.append("release_status pass requires content_qa_status pass")
        if manifest.qa_status.visual_qa_status != PASS:
            errors.append("release_status pass requires visual_qa_status pass")
        if manifest.qa_status.overall_visual_release_status != PASS:
            errors.append("release_status pass requires overall_visual_release_status pass")
        if manifest.decision.release_blockers:
            errors.append("release_status pass requires empty release_blockers")
        if not manifest.decision.accepted_by.strip():
            errors.append("release_status pass requires accepted_by")

    derived = derive_release_status(
        manifest.qa_status.content_qa_status,
        manifest.qa_status.visual_qa_status,
        manifest.decision.release_blockers,
    )
    if manifest.decision.release_status == PASS and derived != PASS:
        errors.append(f"release_status pass conflicts with derived status {derived}")
    return errors


def manifest_to_dict(manifest: MemoReleaseManifest) -> dict[str, Any]:
    return asdict(manifest)


def manifest_from_dict(data: dict[str, Any]) -> MemoReleaseManifest:
    return MemoReleaseManifest(
        memo_id=data.get("memo_id", ""),
        memo_profile=data.get("memo_profile", ""),
        depth_mode=data.get("depth_mode", ""),
        period=data.get("period", ""),
        created_at=data.get("created_at", ""),
        artifact_paths=ReleaseArtifactPaths(**data.get("artifact_paths", {})),
        qa_status=ReleaseQaStatus(**data.get("qa_status", {})),
        decision=ReleaseDecision(**data.get("decision", {})),
        source_commit=data.get("source_commit", ""),
        notes=data.get("notes", ""),
    )


def write_release_manifest(manifest: MemoReleaseManifest, output_path: Path) -> Path:
    errors = validate_release_manifest(manifest)
    if errors:
        raise ValueError("Invalid MemoReleaseManifest: " + "; ".join(errors))
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(manifest_to_dict(manifest), ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path
