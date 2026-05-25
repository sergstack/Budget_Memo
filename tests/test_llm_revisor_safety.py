from __future__ import annotations

import json
from types import SimpleNamespace

from src.regenerate_clean_memo_narratives import MemoTarget
import src.llm_revise_memo_narratives as revisor


def test_revisor_does_not_modify_final_artifacts_by_default(tmp_path, monkeypatch) -> None:
    final_dir = tmp_path / "06_reports" / "memo" / "final"
    final_dir.mkdir(parents=True)
    final_md = final_dir / "accepted_final.md"
    final_docx = final_dir / "accepted_final.docx"
    final_md.write_text("FINAL_MD_SENTINEL", encoding="utf-8")
    final_docx.write_bytes(b"FINAL_DOCX_SENTINEL")

    output_dir = tmp_path / "07_qa" / "llm_revisor"
    output_dir.mkdir(parents=True)
    target = MemoTarget("memo_profile", "standard", final_md, final_docx)

    monkeypatch.setattr(revisor, "PROJECT_ROOT", tmp_path)
    dummy_source = tmp_path / "source.md"
    dummy_source.write_text("source", encoding="utf-8")
    dummy_inputs = SimpleNamespace(
        accepted_package=dummy_source,
        claim_candidates=dummy_source,
        evidence_map=dummy_source,
        chart_catalog=dummy_source,
        report_contract=dummy_source,
        package_qa=dummy_source,
    )

    monkeypatch.setattr(revisor, "pipeline_inputs", lambda _target, _output_dir: dummy_inputs)
    monkeypatch.setattr(revisor, "build_sanitized_input_package", lambda _inputs: ("package", {"status": "ok"}))
    monkeypatch.setattr(revisor, "load_allowed_numbers", lambda _paths: set())
    monkeypatch.setattr(revisor, "build_prompt", lambda *_args, **_kwargs: "prompt")
    monkeypatch.setattr(revisor, "default_ollama_client", lambda *_args, **_kwargs: "# Revised memo\n\nИсточник: test")
    monkeypatch.setattr(revisor, "validate_text", lambda *_args, **_kwargs: {"qa_status": "pass"})

    result = revisor.revise_target(target, output_dir, routing={}, llm_role="russian_revisor")

    assert final_md.read_text(encoding="utf-8") == "FINAL_MD_SENTINEL"
    assert final_docx.read_bytes() == b"FINAL_DOCX_SENTINEL"
    assert result["final_artifacts_modified"] is False
    assert result["output_policy"] == "draft_and_qa_only_no_final_write"

    draft_path = tmp_path / result["draft_md_path"]
    qa_path = tmp_path / result["qa_path"]
    assert draft_path.exists()
    assert qa_path.exists()
    assert "Revised memo" in draft_path.read_text(encoding="utf-8")
    assert json.loads(qa_path.read_text(encoding="utf-8"))["accepted_final_md_path"].endswith("accepted_final.md")
