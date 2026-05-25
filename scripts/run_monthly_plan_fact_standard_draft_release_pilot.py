#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.diagnose_docx_visual_quality import diagnose_docx_visual_quality
from src.memo_display_contract import (
    MemoActionItem,
    MemoBlock,
    MemoChart,
    MemoDisplayContract,
    MemoLimitation,
    MemoSection,
    MemoTable,
    contract_to_dict,
    validate_display_contract,
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


PILOT_DIR_NAME = "monthly_plan_fact_memo__standard__draft_pilot"
MEMO_ID = "monthly_plan_fact_memo__standard__draft"
MEMO_PROFILE = "monthly_plan_fact_memo"
DEPTH_MODE = "standard"
DEFAULT_PERIOD = "2026-04"


@dataclass(frozen=True)
class Memo02DraftSourcePaths:
    readme: Path
    package_qa: Path
    evidence_map: Path
    chart_metadata: Path


def default_source_paths() -> Memo02DraftSourcePaths:
    base = PROJECT_ROOT / "06_reports" / "02_monthly_plan_fact_memo"
    return Memo02DraftSourcePaths(
        readme=base / "README.md",
        package_qa=base / "qa" / "package_qa.md",
        evidence_map=base / "evidence" / "evidence_map.csv",
        chart_metadata=base / "charts" / "chart_metadata.csv",
    )


def run_monthly_plan_fact_standard_draft_release_pilot(
    out_dir: Path,
    source_paths: Memo02DraftSourcePaths | None = None,
    soffice_bin: str | None = None,
) -> dict:
    source_paths = source_paths or default_source_paths()
    pilot_dir = Path(out_dir) / PILOT_DIR_NAME
    pilot_dir.mkdir(parents=True, exist_ok=True)

    docx_path = pilot_dir / f"{MEMO_ID}.docx"
    visual_qa_dir = pilot_dir / "visual_qa"
    manifest_path = pilot_dir / "release_manifest.json"
    contract_path = pilot_dir / "memo_display_contract.json"

    missing_sources = _missing_sources(source_paths)
    if missing_sources:
        manifest = _blocked_manifest(
            docx_path=docx_path,
            visual_qa_path=visual_qa_dir / "defects.json",
            manifest_path=manifest_path,
            blockers=[f"missing_source:{name}" for name in missing_sources],
            notes="Не найдены обязательные исходные файлы memo02 standard; черновой DOCX не создан.",
        )
        write_release_manifest(manifest, manifest_path)
        return {
            "status": "blocked",
            "missing_sources": missing_sources,
            "docx_path": str(docx_path),
            "visual_qa_path": str(visual_qa_dir / "defects.json"),
            "release_manifest_path": str(manifest_path),
            "release_manifest": manifest_to_dict(manifest),
        }

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
            notes="Проверка MemoDisplayContract завершилась ошибкой; черновой DOCX не создан.",
        )
        write_release_manifest(manifest, manifest_path)
        return {
            "status": "blocked",
            "missing_sources": [],
            "docx_path": str(docx_path),
            "visual_qa_path": str(visual_qa_dir / "defects.json"),
            "release_manifest_path": str(manifest_path),
            "release_manifest": manifest_to_dict(manifest),
        }

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
            accepted_by="memo02-standard-draft-pilot" if release_status == "pass" else "",
            rollback="Удалить каталог чернового пилота, переданный через --out.",
        ),
        notes="Черновой пилот memo02 standard; не подключен к промышленной генерации.",
    )
    write_release_manifest(manifest, manifest_path)

    return {
        "status": release_status,
        "missing_sources": [],
        "contract_path": str(contract_path),
        "docx_path": str(docx_path),
        "visual_qa_path": str(visual_qa_dir / "defects.json"),
        "release_manifest_path": str(manifest_path),
        "release_manifest": manifest_to_dict(manifest),
    }


def build_memo02_standard_draft_contract(source_text: dict[str, str], period: str) -> MemoDisplayContract:
    source_rows = [
        ["Описание пакета", "файл найден"],
        ["Проверка пакета", "файл найден"],
        ["Карта подтверждений", "файл найден"],
        ["Каталог графиков", "файл найден"],
    ]
    return MemoDisplayContract(
        memo_id=MEMO_ID,
        memo_profile=MEMO_PROFILE,
        depth_mode=DEPTH_MODE,
        period=period,
        audience="Финансовый директор / операционный директор / управленческие рецензенты",
        title="Ежемесячная записка План-Факт — стандартный черновой пилот",
        subtitle="Черновая проверка цепочки выпуска",
        status_line="Статус: черновой пилот создан вне промышленных папок отчётов.",
        sections=[
            MemoSection(
                section_id="scope",
                title="Область чернового пилота",
                blocks=[
                    MemoBlock(
                        block_type="paragraph",
                        text=(
                            "Этот черновик проверяет цепочку от контракта отображения записки до DOCX, визуальной проверки "
                            "и манифеста выпуска для стандартного профиля ежемесячной записки План-Факт без изменения "
                            "принятых артефактов."
                        ),
                    ),
                    MemoBlock(
                        block_type="bullet_list",
                        bullets=[
                            "Исходные файлы используются только для чтения.",
                            "Промышленный генератор DOCX не вызывается.",
                            "Слои исходных данных, подготовки, витрин, графиков, отчётов и проверок не пересобираются.",
                        ],
                    ),
                    MemoBlock(
                        block_type="table",
                        table=MemoTable(
                            headers=["Источник", "Статус чтения пилотом"],
                            rows=source_rows,
                            caption="Проверяется только наличие источников; финансовые показатели не пересчитываются.",
                        ),
                    ),
                ],
            ),
            MemoSection(
                section_id="source_summary",
                title="Сводка исходного контекста",
                blocks=[
                    MemoBlock(block_type="paragraph", text=_source_presence_note(source_text["readme"], "описание пакета")),
                    MemoBlock(block_type="paragraph", text=_source_presence_note(source_text["package_qa"], "проверка пакета")),
                    MemoBlock(
                        block_type="chart",
                        chart=MemoChart(
                            chart_id="memo02_standard_chart_catalog",
                            title="Каталог графиков",
                            caption="Метаданные графиков прочитаны только как справочный каталог; изображения не встраиваются.",
                        ),
                    ),
                    MemoBlock(
                        block_type="limitation_box",
                        limitation=MemoLimitation(
                            title="Ограничения черновика",
                            text=(
                                "Этот пилот проверяет только механику цепочки выпуска. Он не пересчитывает показатели План-Факт, "
                                "не переинтерпретирует бизнес-логику и не заменяет принятый артефакт записки."
                            ),
                            severity="только цепочка выпуска",
                        ),
                    ),
                    MemoBlock(
                        block_type="action_table",
                        action_items=[
                            MemoActionItem(
                                action="Проверить выходы чернового пилота до любой задачи промышленного подключения.",
                                owner="Сопровождающий репозитория",
                                status="открыто",
                                marker="candidate",
                                evidence_ref="источники чернового пилота memo02 standard",
                            )
                        ],
                    ),
                ],
            ),
        ],
        evidence_references=["memo02_standard_draft_pilot_sources"],
        appendix=[
            MemoBlock(
                block_type="evidence_appendix",
                text="Категории источников, использованные черновым пилотом только для чтения.",
                evidence_refs=["описание пакета", "проверка пакета", "карта подтверждений", "каталог графиков"],
                appendix_only=True,
            )
        ],
    )


def _missing_sources(source_paths: Memo02DraftSourcePaths) -> list[str]:
    missing = []
    for name, path in _source_items(source_paths):
        if not Path(path).is_file():
            missing.append(name)
    return missing


def _read_sources(source_paths: Memo02DraftSourcePaths) -> dict[str, str]:
    return {name: Path(path).read_text(encoding="utf-8", errors="replace") for name, path in _source_items(source_paths)}


def _source_items(source_paths: Memo02DraftSourcePaths) -> list[tuple[str, Path]]:
    return [
        ("readme", source_paths.readme),
        ("package_qa", source_paths.package_qa),
        ("evidence_map", source_paths.evidence_map),
        ("chart_metadata", source_paths.chart_metadata),
    ]


def _detect_period(readme_text: str) -> str:
    for line in readme_text.splitlines():
        normalized = line.strip().lower()
        if "selected month" in normalized and "`" in line:
            parts = line.split("`")
            if len(parts) >= 2 and parts[1].strip():
                return parts[1].strip()
    return DEFAULT_PERIOD


def _source_presence_note(text: str, source_label: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return f"Файл «{source_label}» найден, но не содержит читаемого текста."
    return f"Файл «{source_label}» найден и прочитан в режиме только для чтения."


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
            rollback="Удалить каталог чернового пилота, переданный через --out.",
        ),
        notes=notes,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Run memo02 standard draft-only release pilot.")
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--soffice-bin", default=None)
    parser.add_argument("--readme", type=Path, default=None)
    parser.add_argument("--package-qa", type=Path, default=None)
    parser.add_argument("--evidence-map", type=Path, default=None)
    parser.add_argument("--chart-metadata", type=Path, default=None)
    args = parser.parse_args()

    source_paths = _cli_source_paths(args)
    result = run_monthly_plan_fact_standard_draft_release_pilot(args.out, source_paths, soffice_bin=args.soffice_bin)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "blocked" else 0


def _cli_source_paths(args: argparse.Namespace) -> Memo02DraftSourcePaths | None:
    paths = [args.readme, args.package_qa, args.evidence_map, args.chart_metadata]
    if all(path is None for path in paths):
        return None
    if any(path is None for path in paths):
        raise SystemExit(
            "--readme, --package-qa, --evidence-map, and --chart-metadata must be provided together."
        )
    return Memo02DraftSourcePaths(
        readme=args.readme,
        package_qa=args.package_qa,
        evidence_map=args.evidence_map,
        chart_metadata=args.chart_metadata,
    )


if __name__ == "__main__":
    raise SystemExit(main())
