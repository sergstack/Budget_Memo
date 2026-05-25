from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import run_monthly_plan_fact_standard_draft_release_pilot as pilot


PRODUCTION_GENERATOR_MODULES = {
    "src.regenerate_clean_memo_narratives",
    "src.build_docx_report",
    "src.polish_docx_report",
    "src.build_depth_mode_outputs",
    "src.build_memo02_standard_final",
    "scripts.regenerate_memo01_memo02_ollama_factory",
}


def test_pilot_creates_contract_docx_visual_qa_and_release_manifest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pilot, "diagnose_docx_visual_quality", fake_pass_visual_qa)
    source_paths = write_source_files(tmp_path / "sources")

    result = pilot.run_monthly_plan_fact_standard_draft_release_pilot(tmp_path / "out", source_paths)
    pilot_dir = tmp_path / "out" / pilot.PILOT_DIR_NAME

    assert result["status"] == "pass"
    assert (pilot_dir / "memo_display_contract.json").exists()
    assert (pilot_dir / "monthly_plan_fact_memo__standard__draft.docx").exists()
    assert (pilot_dir / "visual_qa" / "defects.json").exists()
    assert (pilot_dir / "visual_qa" / "diagnostic_report.md").exists()
    assert (pilot_dir / "release_manifest.json").exists()


def test_release_manifest_references_generated_docx_and_visual_qa(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pilot, "diagnose_docx_visual_quality", fake_pass_visual_qa)
    source_paths = write_source_files(tmp_path / "sources")

    result = pilot.run_monthly_plan_fact_standard_draft_release_pilot(tmp_path / "out", source_paths)
    manifest = json.loads(Path(result["release_manifest_path"]).read_text(encoding="utf-8"))

    assert manifest["artifact_paths"]["docx_path"] == result["docx_path"]
    assert manifest["artifact_paths"]["visual_qa_path"] == result["visual_qa_path"]
    assert manifest["artifact_paths"]["release_manifest_path"] == result["release_manifest_path"]


def test_visual_qa_blocked_blocks_release_manifest(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pilot, "diagnose_docx_visual_quality", fake_blocked_visual_qa)
    source_paths = write_source_files(tmp_path / "sources")

    result = pilot.run_monthly_plan_fact_standard_draft_release_pilot(tmp_path / "out", source_paths)
    manifest = json.loads(Path(result["release_manifest_path"]).read_text(encoding="utf-8"))

    assert result["status"] == "blocked"
    assert manifest["decision"]["release_status"] == "blocked"
    assert manifest["qa_status"]["visual_qa_status"] == "blocked"
    assert "VQA-001" in manifest["decision"]["release_blockers"]


def test_pilot_writes_only_under_provided_output_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pilot, "diagnose_docx_visual_quality", fake_pass_visual_qa)
    source_paths = write_source_files(tmp_path / "sources")
    out_dir = tmp_path / "out"
    before = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))

    pilot.run_monthly_plan_fact_standard_draft_release_pilot(out_dir, source_paths)

    after = sorted(path.relative_to(tmp_path) for path in tmp_path.rglob("*"))
    created = [path for path in after if path not in before]
    assert created
    assert all(path == Path("out") or path.is_relative_to(Path("out")) for path in created)


def test_missing_required_source_blocks_without_creating_fake_source_data(tmp_path: Path) -> None:
    source_paths = write_source_files(tmp_path / "sources")
    source_paths.evidence_map.unlink()

    result = pilot.run_monthly_plan_fact_standard_draft_release_pilot(tmp_path / "out", source_paths)
    pilot_dir = tmp_path / "out" / pilot.PILOT_DIR_NAME

    assert result["status"] == "blocked"
    assert result["missing_sources"] == ["evidence_map"]
    assert not source_paths.evidence_map.exists()
    assert not (pilot_dir / "memo_display_contract.json").exists()
    assert not (pilot_dir / "monthly_plan_fact_memo__standard__draft.docx").exists()
    assert (pilot_dir / "release_manifest.json").exists()


def test_production_generators_are_not_imported_or_called(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pilot, "diagnose_docx_visual_quality", fake_pass_visual_qa)
    source_paths = write_source_files(tmp_path / "sources")
    before = set(sys.modules)

    pilot.run_monthly_plan_fact_standard_draft_release_pilot(tmp_path / "out", source_paths)

    imported = set(sys.modules) - before
    assert PRODUCTION_GENERATOR_MODULES.isdisjoint(imported)


def test_script_executes_by_file_path_with_fixture_sources(tmp_path: Path) -> None:
    source_paths = write_source_files(tmp_path / "sources")
    out_dir = tmp_path / "out"
    script = Path("scripts/run_monthly_plan_fact_standard_draft_release_pilot.py")
    command = [
        sys.executable,
        str(script),
        "--out",
        str(out_dir),
        "--readme",
        str(source_paths.readme),
        "--package-qa",
        str(source_paths.package_qa),
        "--evidence-map",
        str(source_paths.evidence_map),
        "--chart-metadata",
        str(source_paths.chart_metadata),
    ]

    completed = subprocess.run(command, cwd=Path.cwd(), capture_output=True, text=True, check=False)

    assert completed.returncode in {0, 2}
    assert "ModuleNotFoundError" not in completed.stderr
    assert (out_dir / pilot.PILOT_DIR_NAME / "release_manifest.json").exists()


def write_source_files(root: Path) -> pilot.Memo02DraftSourcePaths:
    readme = root / "06_reports" / "02_monthly_plan_fact_memo" / "README.md"
    package_qa = root / "06_reports" / "02_monthly_plan_fact_memo" / "qa" / "package_qa.md"
    evidence_map = root / "06_reports" / "02_monthly_plan_fact_memo" / "evidence" / "evidence_map.csv"
    chart_metadata = root / "06_reports" / "02_monthly_plan_fact_memo" / "charts" / "chart_metadata.csv"
    for path in [readme, package_qa, evidence_map, chart_metadata]:
        path.parent.mkdir(parents=True, exist_ok=True)
    readme.write_text(
        "# Memo 02\n\n- memo profile: `monthly_plan_fact_memo`\n- selected month: `2026-04`\n",
        encoding="utf-8",
    )
    package_qa.write_text("# Package QA\n\nstatus: pass\n", encoding="utf-8")
    evidence_map.write_text("evidence_id,source\nEV-001,fixture\n", encoding="utf-8")
    chart_metadata.write_text("chart_id,title\nCH-001,Fixture chart\n", encoding="utf-8")
    return pilot.Memo02DraftSourcePaths(
        readme=readme,
        package_qa=package_qa,
        evidence_map=evidence_map,
        chart_metadata=chart_metadata,
    )


def fake_pass_visual_qa(docx_path: Path, out_dir: Path, soffice_bin: str | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "verdicts": {
            "docx_render_status": "pass",
            "visual_layout_status": "pass",
            "executive_readability_status": "pass",
            "publishing_hygiene_status": "pass",
            "overall_visual_release_status": "pass",
        },
        "release_blockers": [],
        "defects": [],
    }
    (out_dir / "defects.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "diagnostic_report.md").write_text("# fake visual qa\n", encoding="utf-8")
    return payload


def fake_blocked_visual_qa(docx_path: Path, out_dir: Path, soffice_bin: str | None = None) -> dict:
    out_dir.mkdir(parents=True, exist_ok=True)
    payload = {
        "verdicts": {
            "docx_render_status": "blocked",
            "visual_layout_status": "pass",
            "executive_readability_status": "pass",
            "publishing_hygiene_status": "pass",
            "overall_visual_release_status": "blocked",
        },
        "release_blockers": [{"id": "VQA-001", "description": "LibreOffice/soffice is unavailable."}],
        "defects": [],
    }
    (out_dir / "defects.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (out_dir / "diagnostic_report.md").write_text("# fake visual qa\n", encoding="utf-8")
    return payload
