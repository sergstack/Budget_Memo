#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from scripts.diagnose_docx_visual_quality import diagnose_docx_visual_quality
from src.memo_display_contract import (
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


MEMO_ID = "monthly_plan_fact_memo__standard__analytical_draft"
MEMO_PROFILE = "monthly_plan_fact_memo"
DEPTH_MODE = "standard"
DEFAULT_PERIOD = "2026-04"
DOCX_NAME = "monthly_plan_fact_memo__standard__analytical_draft.docx"
DRAFT_FLOW_ROOT = PROJECT_ROOT / "artifacts" / "draft_flows" / "memo02_standard_analytical"


@dataclass(frozen=True)
class Memo02AnalyticalSourcePaths:
    final_md: Path
    ollama_revisor_md: Path
    package_qa: Path
    evidence_map: Path
    standard_chart_metadata: Path
    chart_manifest: Path
    chart_metadata_csv: Path


def default_source_paths() -> Memo02AnalyticalSourcePaths:
    base = PROJECT_ROOT / "06_reports" / "02_monthly_plan_fact_memo"
    return Memo02AnalyticalSourcePaths(
        final_md=base / "final" / "02_monthly_plan_fact_memo__standard__2026-04__final.md",
        ollama_revisor_md=base / "ollama_variants" / "02_monthly_plan_fact_memo__standard__ollama_revisor.md",
        package_qa=base / "qa" / "package_qa.md",
        evidence_map=base / "evidence" / "evidence_map.csv",
        standard_chart_metadata=base / "charts" / "standard_final" / "standard_final_chart_metadata.json",
        chart_manifest=base / "charts" / "chart_manifest.json",
        chart_metadata_csv=base / "charts" / "chart_metadata.csv",
    )


def default_output_dir(now: datetime | None = None) -> Path:
    timestamp = (now or datetime.now(timezone.utc)).strftime("%Y%m%d_%H%M%SZ")
    return DRAFT_FLOW_ROOT / timestamp


def run_memo02_standard_analytical_draft_release_flow(
    out_dir: Path | None = None,
    source_paths: Memo02AnalyticalSourcePaths | None = None,
    soffice_bin: str | None = None,
    run_ollama: bool = False,
    allow_existing_narrative_fallback: bool = False,
    now: datetime | None = None,
) -> dict:
    source_paths = source_paths or default_source_paths()
    output_dir = Path(out_dir) if out_dir is not None else default_output_dir(now)
    output_dir.mkdir(parents=True, exist_ok=True)

    contract_path = output_dir / "memo_display_contract.json"
    docx_path = output_dir / DOCX_NAME
    visual_qa_dir = output_dir / "visual_qa"
    manifest_path = output_dir / "release_manifest.json"
    interpretations_path = output_dir / "chart_interpretations.json"
    narrative_source_path = output_dir / "narrative_source.md"

    missing_sources = _missing_sources(source_paths)
    if missing_sources:
        manifest = _blocked_manifest(
            docx_path,
            visual_qa_dir / "defects.json",
            manifest_path,
            [f"missing_source:{name}" for name in missing_sources],
            "Не найдены обязательные принятые артефакты стандартной записки План-Факт; аналитический черновой поток остановлен.",
        )
        write_release_manifest(manifest, manifest_path)
        return _result("blocked", output_dir, contract_path, docx_path, visual_qa_dir, manifest_path, manifest, missing_sources)

    if run_ollama:
        blockers = ["ollama_generation_not_implemented_in_draft_flow_v1"]
        notes = "Режим Ollama запрошен явно, но безопасная черновая интеграция без финальных записей в этой версии не реализована."
        if not allow_existing_narrative_fallback:
            manifest = _blocked_manifest(docx_path, visual_qa_dir / "defects.json", manifest_path, blockers, notes)
            write_release_manifest(manifest, manifest_path)
            return _result("blocked", output_dir, contract_path, docx_path, visual_qa_dir, manifest_path, manifest, [])

    narrative = _select_narrative(source_paths, prefer_ollama=run_ollama and allow_existing_narrative_fallback)
    chart_rows = _load_chart_rows(source_paths.standard_chart_metadata)
    chart_interpretations = [_chart_interpretation(row) for row in chart_rows]
    interpretations_path.write_text(json.dumps(chart_interpretations, ensure_ascii=False, indent=2), encoding="utf-8")
    narrative_source_path.write_text(narrative, encoding="utf-8")

    contract = build_memo02_standard_analytical_contract(narrative, chart_rows, chart_interpretations, DEFAULT_PERIOD)
    contract_errors = validate_display_contract(contract)
    if contract_errors:
        manifest = _blocked_manifest(
            docx_path,
            visual_qa_dir / "defects.json",
            manifest_path,
            [f"contract_validation:{error}" for error in contract_errors],
            "Проверка контракта отображения завершилась ошибкой; аналитический черновой поток остановлен.",
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
            content_qa_path=str(interpretations_path),
            visual_qa_path=str(visual_qa_dir / "defects.json"),
            release_manifest_path=str(manifest_path),
        ),
        qa_status=ReleaseQaStatus(
            content_qa_status=content_qa_status,
            visual_qa_status=visual_qa_status,
            overall_visual_release_status=visual_qa_status,
        ),
        decision=ReleaseDecision(
            release_status=release_status,
            release_blockers=release_blockers,
            accepted_by="memo02-standard-analytical-draft-flow" if release_status == "pass" else "",
            rollback="Удалить выходной каталог аналитического чернового потока.",
        ),
        notes="Аналитический черновик стандартной записки План-Факт; ручное согласование и публикация выполняются отдельными командами.",
    )
    write_release_manifest(manifest, manifest_path)
    return _result(release_status, output_dir, contract_path, docx_path, visual_qa_dir, manifest_path, manifest, [])


def build_memo02_standard_analytical_contract(
    source_text: str,
    chart_rows: list[dict],
    chart_interpretations: list[dict],
    period: str,
) -> MemoDisplayContract:
    findings = _extract_key_findings(source_text)
    chart_blocks = [
        _chart_block(row, interpretation)
        for row, interpretation in zip(chart_rows, chart_interpretations)
    ]
    return MemoDisplayContract(
        memo_id=MEMO_ID,
        memo_profile=MEMO_PROFILE,
        depth_mode=DEPTH_MODE,
        period=period,
        audience="Финансовый директор / операционный директор / управленческие рецензенты",
        title="Ежемесячная аналитическая записка План-Факт за апрель 2026",
        subtitle="Аналитический черновик на основе принятых артефактов",
        status_line="Статус: черновой аналитический выпуск; ручное согласование обязательно до публикации.",
        sections=[
            MemoSection(
                section_id="purpose",
                title="Цель записки",
                blocks=[
                    MemoBlock(
                        block_type="paragraph",
                        text=(
                            "Записка собирает управленческий черновик по стандартному профилю План-Факт из уже принятых "
                            "материалов стандартной записки План-Факт. Черновик не пересчитывает показатели и не заменяет "
                            "финальные материалы."
                        ),
                    )
                ],
            ),
            MemoSection(
                section_id="period_sources",
                title="Период и статус источников",
                blocks=[
                    MemoBlock(
                        block_type="paragraph",
                        text=(
                            "Период анализа — апрель 2026. Используются принятые текстовые, графические и проверочные "
                            "артефакты стандартной записки План-Факт в режиме только для чтения."
                        ),
                    ),
                    MemoBlock(
                        block_type="table",
                        table=MemoTable(
                            headers=["Источник", "Назначение"],
                            rows=[
                                ["Финальный текст стандартной записки", "Базовый управленческий текст без нового расчёта"],
                                ["Карта подтверждений", "Трассировка фактов, ограничений и источников"],
                                ["Реестр графиков стандартного пакета", "Названия, изображения, источники и ограничения графиков"],
                                ["Проверка пакета", "Подтверждение статуса исходного пакета"],
                            ],
                        ),
                    ),
                ],
            ),
            MemoSection(
                section_id="findings",
                title="Ключевые выводы",
                blocks=[MemoBlock(block_type="bullet_list", bullets=findings)],
            ),
            MemoSection(
                section_id="plan_fact_meaning",
                title="План-Факт: смысл отклонения",
                blocks=[
                    MemoBlock(
                        block_type="paragraph",
                        text=(
                            "Отклонение читается как План минус Факт. Положительное значение означает факт ниже плана, "
                            "отрицательное значение означает факт выше плана, а абсолютное отклонение показывает масштаб "
                            "проверки, но не подтверждает причину."
                        ),
                    )
                ],
            ),
            MemoSection(
                section_id="charts",
                title="Графики и интерпретации",
                blocks=[
                    *chart_blocks,
                ],
            ),
            MemoSection(
                section_id="limitations",
                title="Ограничения",
                blocks=[
                    MemoBlock(
                        block_type="limitation_box",
                        limitation=MemoLimitation(
                            title="Границы аналитического черновика",
                            text=(
                                "Черновик не выполняет пересчёт данных, не подтверждает причины отклонений без владельцев "
                                "бюджета и не переводит кандидаты проверки в утверждённый план действий."
                            ),
                            severity="ручная проверка обязательна",
                        ),
                    )
                ],
            ),
            MemoSection(
                section_id="next_actions",
                title="Следующие действия",
                blocks=[
                    MemoBlock(
                        block_type="table",
                        table=MemoTable(
                            headers=["Действие", "Ответственный", "Статус", "Подтверждение"],
                            rows=[
                                [
                                    "Проверить текст, графики, визуальную диагностику и манифест перед ручным согласованием",
                                    "Сопровождающий репозитория",
                                    "кандидат",
                                    "принятые материалы стандартной записки План-Факт и визуальная проверка",
                                ]
                            ],
                            caption="Финальное продвижение не выполняется этим потоком.",
                        ),
                    )
                ],
            ),
        ],
        evidence_references=["memo02_standard_final_text", "standard_final_chart_metadata", "evidence_map", "package_qa"],
        appendix=[
            MemoBlock(
                block_type="evidence_appendix",
                text=(
                    "Приложение фиксирует источники, использованные для чернового аналитического выпуска: "
                    "финальный текст стандартной записки, карта подтверждений, реестр графиков стандартного пакета "
                    "и проверка пакета."
                ),
                evidence_refs=[
                    "финальный текст стандартной записки",
                    "карта подтверждений",
                    "реестр графиков стандартного пакета",
                    "проверка пакета",
                ],
                appendix_only=True,
            )
        ],
    )


def _missing_sources(source_paths: Memo02AnalyticalSourcePaths) -> list[str]:
    missing = []
    for name, path in _source_items(source_paths):
        if not Path(path).is_file():
            missing.append(name)
    return missing


def _source_items(source_paths: Memo02AnalyticalSourcePaths) -> list[tuple[str, Path]]:
    return [
        ("final_md", source_paths.final_md),
        ("package_qa", source_paths.package_qa),
        ("evidence_map", source_paths.evidence_map),
        ("standard_chart_metadata", source_paths.standard_chart_metadata),
        ("chart_manifest", source_paths.chart_manifest),
        ("chart_metadata_csv", source_paths.chart_metadata_csv),
    ]


def _select_narrative(source_paths: Memo02AnalyticalSourcePaths, prefer_ollama: bool) -> str:
    if prefer_ollama and source_paths.ollama_revisor_md.is_file():
        return source_paths.ollama_revisor_md.read_text(encoding="utf-8", errors="replace")
    return source_paths.final_md.read_text(encoding="utf-8", errors="replace")


def _load_chart_rows(path: Path) -> list[dict]:
    rows = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(rows, list):
        raise ValueError("standard chart metadata must be a JSON list")
    return [dict(row) for row in rows]


def _chart_interpretation(row: dict) -> dict:
    title = _polish_visible_terms(str(row.get("title_ru", "")).strip())
    source = _polish_visible_terms(str(row.get("source", "")).strip())
    limitation = _polish_visible_terms(str(row.get("limitation", "")).strip())
    check = _chart_check_action(title)
    return {
        "chart_id": str(row.get("chart_id", "")),
        "title": title,
        "what_shows": f"Показывает выбранный разрез стандартной записки План-Факт: {title.lower()}.",
        "management_meaning": f"Помогает определить маршрут управленческого просмотра. Источник: {source}.",
        "what_to_check": check,
        "limitation": limitation,
    }


def _chart_block(row: dict, interpretation: dict) -> MemoBlock:
    title = _polish_visible_terms(str(row.get("title_ru", "")).strip()) or "График стандартного пакета"
    caption = "\n".join(
        [
            f"Что показывает график: {interpretation['what_shows']}",
            f"Управленческий смысл: {interpretation['management_meaning']}",
            f"Что проверить: {interpretation['what_to_check']}",
            f"Ограничение: {interpretation['limitation']}",
        ]
    )
    return MemoBlock(
        block_type="chart",
        chart=MemoChart(
            chart_id=str(row.get("chart_id", "")),
            title=title,
            caption=caption,
            source_ref=str((PROJECT_ROOT / str(row.get("image_path", ""))).resolve()),
        ),
    )


def _chart_check_action(title: str) -> str:
    normalized = title.lower()
    if "планирования" in normalized:
        return "Сверить, какие группы дают частый сигнал и какие группы дают наибольший денежный масштаб."
    if "стать" in normalized or "отклон" in normalized:
        return "Проверить верхние статьи по модулю отклонения и отдельно посмотреть знак отклонения."
    if "цфо" in normalized:
        return "Согласовать маршрут просмотра с ответственным ЦФО и проверить связку ЦФО со статьёй."
    if "факт без плана" in normalized or "план без факта" in normalized:
        return "Разделить неполноту планирования, перенос периода и возможную ошибку классификации."
    if "контрагент" in normalized:
        return "Проверить первичные строки по контрагентам с наибольшим вкладом в модуль отклонения."
    if "юрлица" in normalized or "валют" in normalized:
        return "Проверить, не связан ли сигнал с юридическим лицом, валютой или способом отражения операции."
    return "Проверить первичные строки и подтверждения владельцев бюджета перед управленческим выводом."


def _extract_key_findings(narrative: str) -> list[str]:
    lines = []
    for raw in narrative.splitlines():
        text = re.sub(r"^[#\\-\\s]+", "", raw).strip()
        if not text or text.startswith("|"):
            continue
        if _looks_like_heading(text):
            continue
        if any(marker in text.lower() for marker in ["план", "факт", "отклон", "цфо", "провер"]):
            cleaned = _polish_visible_terms(_strip_markdown(text))
            if cleaned not in lines:
                lines.append(cleaned)
        if len(lines) >= 4:
            break
    if lines:
        return lines
    return [
        "Итог периода близок к плану, но структура отклонений требует управленческого просмотра.",
        "Основной маршрут проверки проходит через статьи, ЦФО, факт без плана и план без факта.",
        "Причины отклонений не подтверждаются без комментариев владельцев бюджета.",
    ]


def _strip_markdown(text: str) -> str:
    text = re.sub(r"`([^`]+)`", r"\1", text)
    text = re.sub(r"\\*\\*([^*]+)\\*\\*", r"\1", text)
    return _polish_visible_terms(text.strip())


def _looks_like_heading(text: str) -> bool:
    return len(text) <= 80 and not text.endswith(".") and not text.endswith("!") and not text.endswith("?")


def _polish_visible_terms(text: str) -> str:
    replacements = {
        "memo02": "стандартная записка План-Факт",
        "Memo02": "стандартная записка План-Факт",
        "Delta": "отклонение",
        "ABS": "модуль отклонения",
        "Word": "документ",
        "narrative": "управленческий текст",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    return text


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
            rollback="Удалить выходной каталог аналитического чернового потока.",
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
    parser = argparse.ArgumentParser(description="Run memo02 standard analytical draft release flow.")
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--soffice-bin", default=None)
    parser.add_argument("--run-ollama", action="store_true")
    parser.add_argument("--allow-existing-narrative-fallback", action="store_true")
    args = parser.parse_args()

    result = run_memo02_standard_analytical_draft_release_flow(
        out_dir=args.out,
        soffice_bin=args.soffice_bin,
        run_ollama=args.run_ollama,
        allow_existing_narrative_fallback=args.allow_existing_narrative_fallback,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 2 if result["status"] == "blocked" else 0


if __name__ == "__main__":
    raise SystemExit(main())
