#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from scripts.diagnose_docx_visual_quality import diagnose_docx_visual_quality
from src.memo_display_contract import (
    MemoActionItem,
    MemoBlock,
    MemoChart,
    MemoDisplayContract,
    MemoKpiCard,
    MemoLimitation,
    MemoSection,
    MemoTable,
)
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


def build_synthetic_contract() -> MemoDisplayContract:
    return MemoDisplayContract(
        memo_id="synthetic_memo_release_pilot",
        memo_profile="synthetic_profile",
        depth_mode="standard",
        period="2026-04",
        audience="Проверка выпуска",
        title="Синтетический пилот выпуска записки",
        subtitle="Только синтетические данные",
        status_line="Статус: тестовый пилот",
        sections=[
            MemoSection(
                section_id="summary",
                title="Управленческое резюме",
                blocks=[
                    MemoBlock(block_type="paragraph", text="Синтетический абзац для проверки цепочки выпуска."),
                    MemoBlock(block_type="bullet_list", bullets=["Синтетический вывод", "Синтетический риск"]),
                    MemoBlock(
                        block_type="kpi_cards",
                        kpi_cards=[MemoKpiCard(label="Синтетический показатель", value="100", status="тест")],
                    ),
                    MemoBlock(
                        block_type="table",
                        table=MemoTable(headers=["Показатель", "Значение"], rows=[["Синтетический показатель", "100"]]),
                    ),
                    MemoBlock(
                        block_type="chart",
                        chart=MemoChart(chart_id="synthetic_chart_01", title="Синтетический график"),
                    ),
                    MemoBlock(
                        block_type="limitation_box",
                        limitation=MemoLimitation(title="Ограничения", text="Используются только синтетические данные."),
                    ),
                    MemoBlock(
                        block_type="action_table",
                        action_items=[
                            MemoActionItem(
                                action="Проверить выход пилота",
                                owner="Проверка качества",
                                status="открыто",
                                marker="candidate",
                                evidence_ref="синтетическое подтверждение 01",
                            )
                        ],
                    ),
                ],
            )
        ],
        appendix=[
            MemoBlock(
                block_type="evidence_appendix",
                text="Синтетическое приложение с подтверждениями.",
                evidence_refs=["синтетическое подтверждение 01"],
                appendix_only=True,
            )
        ],
    )


def run_synthetic_memo_release_pilot(out_dir: Path, soffice_bin: str | None = None) -> dict:
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    docx_path = out_dir / "synthetic_memo_release_pilot.docx"
    visual_qa_dir = out_dir / "visual_qa"
    manifest_path = out_dir / "release_manifest.json"

    contract = build_synthetic_contract()
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
            accepted_by="synthetic-pilot" if release_status == "pass" else "",
            rollback="Удалить каталог синтетического пилота.",
        ),
        notes="Синтетический пилот выпуска записки; не производственные данные.",
    )
    write_release_manifest(manifest, manifest_path)

    return {
        "docx_path": str(docx_path),
        "visual_qa_path": str(visual_qa_dir / "defects.json"),
        "release_manifest_path": str(manifest_path),
        "release_manifest": manifest_to_dict(manifest),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Run synthetic MemoDisplayContract -> DOCX -> Visual QA -> Release Manifest pilot.")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--soffice-bin", default=None)
    args = parser.parse_args()

    result = run_synthetic_memo_release_pilot(args.out, soffice_bin=args.soffice_bin)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
