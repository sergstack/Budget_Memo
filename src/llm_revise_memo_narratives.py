from __future__ import annotations

import argparse
import csv
import json
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from src.qa_ollama_outputs import QaContext, load_allowed_numbers, validate_text
from src.regenerate_clean_memo_narratives import PROJECT_ROOT, TARGETS, MemoTarget
from src.run_ollama_memo_pipeline import (
    OllamaUnavailable,
    build_sanitized_input_package,
    default_ollama_client,
    filter_memo_body,
    load_routing,
    model_metadata,
    PipelineInputs,
)


INPUT_DIR = PROJECT_ROOT / "07_qa/llm_narrative_qa/full_sweep_20260522_0153_final_docx_all8/inputs"


@dataclass(frozen=True)
class RevisorSources:
    accepted_package: Path
    claim_candidates: Path
    evidence_map: Path
    chart_catalog: Path
    report_contract: Path
    package_qa: Path


def target_sources(target: MemoTarget) -> RevisorSources:
    if target.direction == "executive_yoy_mom_budget_memo":
        claims = {
            "short": "m1_short_claims.md",
            "standard": "m1_standard_claims.md",
            "deep": "m1_standard_claims.md",
            "action": "m1_action_claims.md",
        }[target.depth]
        package = INPUT_DIR / f"{target.direction}__{target.depth}__primary_package.md"
        return RevisorSources(
            accepted_package=package,
            claim_candidates=INPUT_DIR / claims,
            evidence_map=package,
            chart_catalog=package,
            report_contract=PROJECT_ROOT / "06_reports/01_executive_yoy_mom_budget_memo/README.md",
            package_qa=PROJECT_ROOT / "06_reports/01_executive_yoy_mom_budget_memo/qa/memo_01__depth_outputs_qa_summary.md",
        )
    claims = {
        "short": "m2_short_claims.md",
        "standard": "monthly_plan_fact_memo__standard__primary_package.md",
        "deep": "monthly_plan_fact_memo__deep__primary_package.md",
        "action": "m2_action_claims.md",
    }[target.depth]
    package = INPUT_DIR / f"{target.direction}__{target.depth}__primary_package.md"
    return RevisorSources(
        accepted_package=package,
        claim_candidates=INPUT_DIR / claims,
        evidence_map=PROJECT_ROOT / "06_reports/02_monthly_plan_fact_memo/evidence/evidence_map.csv",
        chart_catalog=PROJECT_ROOT / "06_reports/02_monthly_plan_fact_memo/charts/chart_metadata.csv",
        report_contract=PROJECT_ROOT / "06_reports/02_monthly_plan_fact_memo/README.md",
        package_qa=PROJECT_ROOT / "06_reports/02_monthly_plan_fact_memo/qa/package_qa.md",
    )


def pipeline_inputs(target: MemoTarget, output_dir: Path) -> PipelineInputs:
    sources = target_sources(target)
    return PipelineInputs(
        memo_profile=target.direction,
        depth_mode=target.depth,
        accepted_package=sources.accepted_package,
        claim_candidates=sources.claim_candidates,
        evidence_map=sources.evidence_map,
        chart_catalog=sources.chart_catalog,
        report_contract=sources.report_contract,
        package_qa=sources.package_qa,
        output_dir=output_dir,
        accepted_final_docx=target.docx_path,
        accepted_final_md=target.md_path,
    )


def strip_markdown_response(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL | re.IGNORECASE).strip()
    fenced = re.match(r"^```(?:markdown|md)?\s*(.*?)\s*```$", text, flags=re.DOTALL | re.IGNORECASE)
    if fenced:
        text = fenced.group(1).strip()
    return filter_memo_body(text)


def csv_table(path: Path, columns: list[str], limit: int = 5) -> str:
    if not path.exists():
        return ""
    with path.open(encoding="utf-8-sig", newline="") as fh:
        rows = list(csv.DictReader(fh))[:limit]
    if not rows:
        return ""
    lines = ["| " + " | ".join(columns) + " |", "| " + " | ".join(["---"] * len(columns)) + " |"]
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(col, "")).strip() for col in columns) + " |")
    return "\n".join(lines)


def business_fact_brief(target: MemoTarget) -> str:
    if target.direction == "monthly_plan_fact_memo":
        base = PROJECT_ROOT / "06_reports/02_monthly_plan_fact_memo/charts/standard_final/data"
        mgmt = PROJECT_ROOT / "06_reports/02_monthly_plan_fact_memo/charts/management_depth/data"
        return "\n\n".join(
            part
            for part in [
                "### Primary KPI/source facts for memo02",
                "Top article deviations:\n" + csv_table(base / "top_deviations_by_article.csv", ["Статья 1", "Статья", "План EUR", "Факт EUR", "Delta EUR", "ABS Delta EUR", "Исполнение %", "Статус"], 7),
                "CFO concentration:\n" + csv_table(mgmt / "cfo_abs_delta.csv", ["cfo", "plan_eur", "fact_eur", "delta_eur", "abs_delta_eur", "execution_pct", "status"], 6),
                "CFO x article localization:\n" + csv_table(base / "direction_level_cfo_article.csv", ["ЦФО", "Статья 1", "Статья", "План EUR", "Факт EUR", "Delta EUR", "ABS Delta EUR", "Приоритет проверки"], 6),
                "Counterparty localization:\n" + csv_table(base / "counterparty_localization.csv", ["Контрагент", "ЦФО", "Статья", "План EUR", "Факт EUR", "Delta EUR", "ABS Delta EUR", "Ограничение качества"], 5),
            ]
            if part.strip()
        )
    package = (INPUT_DIR / f"{target.direction}__{target.depth}__primary_package.md").read_text(encoding="utf-8")
    claims = target_sources(target).claim_candidates.read_text(encoding="utf-8") if target_sources(target).claim_candidates.exists() else ""
    markers = [
        "ONJN Gaming Tax",
        "Avento MT",
        "Advertisement Dept Main",
        "Роялти",
        "Atlant",
        "YoY",
        "MoM",
        "Плановый риск",
        "IN context",
    ]
    selected = []
    for line in (claims + "\n" + package).splitlines():
        if any(marker.lower() in line.lower() for marker in markers):
            selected.append(line.strip())
        if len(selected) >= 45:
            break
    return "### Primary KPI/source facts for memo01\n" + "\n".join(f"- {line}" for line in selected if line)


def compact_qa_feedback(result: dict) -> str:
    if not result or result.get("qa_status") == "pass":
        return "text_qa: pass"
    parts = []
    for key in [
        "unsupported_claims",
        "new_numeric_claims",
        "causality_violations",
        "action_maturity_violations",
        "language_violations",
        "formula_semantics_violations",
        "chart_caption_violations",
    ]:
        values = result.get(key) or []
        if values:
            parts.append(f"{key}: {json.dumps(values[:12], ensure_ascii=False)}")
    if result.get("limitation_visibility_status") != "pass":
        parts.append("limitation_visibility_status: fail")
    return "\n".join(parts) or json.dumps(result, ensure_ascii=False)[:2000]


def depth_contract(target: MemoTarget) -> str:
    if target.depth == "short":
        return "short: 450-650 Russian words, compact executive brief, KPI table, 3-5 findings, one risk/action table."
    if target.depth == "standard":
        return "standard: 900-1300 Russian words, full management memo, KPI block, interpretation after tables, risk table, action table, appendix."
    if target.depth == "deep":
        return "deep: 1100-1600 Russian words, finance working package, decomposition by object/dimension, evidence notes, definitions, limitations."
    return "action: 700-1000 Russian words, candidate action tracker, basis/evidence/limitation/status, priority, route, deadline/status when available."


def build_prompt(target: MemoTarget, package: str, current_md: str, feedback: str, pass_no: int) -> str:
    memo02_rules = ""
    if target.direction == "monthly_plan_fact_memo":
        memo02_rules = "\n".join(
            [
                "- Include exactly these formula semantics in Russian:",
                "  `Delta EUR = Plan EUR - Fact EUR`.",
                "  `Положительная Delta = факт ниже плана`.",
                "  `Отрицательная Delta = факт выше плана`.",
                "  `ABS Delta показывает масштаб отклонения`.",
            ]
        )
    return f"""Ты LLM-редактор управленческой аналитической записки.

Задача: переписать финальный Markdown для memo_profile={target.direction}, depth={target.depth}.
Это целевой LLM-authored / LLM-revised финальный narrative. Не возвращай JSON.

Жесткие правила:
- Используй только факты из SOURCES ниже.
- Не добавляй новые числа, проценты, ранги, суммы, даты и формулы вне SOURCES.
- Не придумывай причины, владельцев, сроки или статусы действий.
- Не вставляй runtime, pipeline, QA status, код, пути файлов, имена папок, технические инструкции.
- Не используй технические ID в основном тексте.
- Каждое длинное утверждение должно содержать маркер `Источник:` или `Ограничение:` или `требует проверки`.
- Действия формулируй только как кандидаты проверки или маршрут ревью, если срок и статус не подтверждены.
- Видимо покажи раздел `## Ограничения`.
- Не заявляй production readiness.
- Если упоминаешь плановый риск, явно напиши точную фразу: `плановый риск не факт исполнения`.
- Для executive_yoy_mom_budget_memo лучше не используй словосочетание `плановый риск`; пиши `плановая база` или `плановые сигналы`, если это не искажает смысл.
{memo02_rules}

Business-reference depth:
- Не пиши короткий QA-safe skeleton.
- Используй стиль бизнес-дайджеста: конкретный executive summary, KPI block, таблицы, интерпретация после таблиц, риск-зоны, action tracker, приложение.
- Не копируй PSP-метрики и не упоминай reference document; перенеси только структуру в бюджетный домен.
- Depth contract: {depth_contract(target)}

Целевая структура:
# <русский заголовок>
## Итог периода
## Ключевые показатели
## Основные отклонения и локализация
## Риски и зоны проверки
## Действия и ручные проверки
## Приложение: топы, определения, ограничения

Таблицы нужны обязательно. Табличные строки должны брать значения только из PRIMARY_FACT_BRIEF/SOURCES. После каждой таблицы дай 1-2 абзаца интерпретации с `Источник:` или `Ограничение:`.

QA feedback from previous pass:
{feedback}

PRIMARY_FACT_BRIEF:
{business_fact_brief(target)[:10000]}

CURRENT_DRAFT:
{current_md[:6000]}

SOURCES:
{package[:14000]}

Верни только Markdown финальной записки. Попытка: {pass_no}.
"""


def revisor_output_paths(target: MemoTarget, output_dir: Path) -> tuple[Path, Path]:
    stem = f"{target.direction}__{target.depth}__llm_revisor"
    return output_dir / f"{stem}.md", output_dir / f"{stem}_qa.json"


def revise_target(target: MemoTarget, output_dir: Path, routing: dict, llm_role: str) -> dict:
    inputs = pipeline_inputs(target, output_dir)
    package, sanitization_report = build_sanitized_input_package(inputs)
    allowed_numbers = load_allowed_numbers(
        [
            inputs.accepted_package,
            inputs.claim_candidates,
            inputs.evidence_map,
            inputs.chart_catalog,
            inputs.report_contract,
            inputs.package_qa,
        ]
    )
    context = QaContext(allowed_numbers=allowed_numbers, memo_profile=target.direction)
    current_md = target.md_path.read_text(encoding="utf-8") if target.md_path.exists() else ""
    attempts = []
    feedback = "initial LLM revisor pass"
    final_text = ""
    final_qa: dict = {}
    final_metadata: dict = {}
    for pass_no in [1, 2]:
        prompt = build_prompt(target, package, current_md, feedback, pass_no)
        response = default_ollama_client(llm_role, prompt, routing)
        metadata = model_metadata(response)
        revised = strip_markdown_response(str(response))
        qa = validate_text(revised, context)
        attempts.append(
            {
                "pass": pass_no,
                "model_metadata": metadata,
                "text_qa": qa,
                "output_chars": len(revised),
            }
        )
        final_text = revised
        final_qa = qa
        final_metadata = metadata
        if qa["qa_status"] == "pass":
            break
        current_md = revised
        feedback = compact_qa_feedback(qa)
    draft_md_path, qa_path = revisor_output_paths(target, output_dir)
    draft_md_path.write_text(final_text, encoding="utf-8")
    result = {
        "direction": target.direction,
        "depth": target.depth,
        "draft_md_path": str(draft_md_path.relative_to(PROJECT_ROOT)),
        "qa_path": str(qa_path.relative_to(PROJECT_ROOT)),
        "accepted_final_md_path": str(target.md_path.relative_to(PROJECT_ROOT)),
        "accepted_final_docx_path": str(target.docx_path.relative_to(PROJECT_ROOT)),
        "final_artifacts_modified": False,
        "text_qa_status": final_qa.get("qa_status"),
        "attempts": attempts,
        "final_model_metadata": final_metadata,
        "sanitization_report": sanitization_report,
        "authoring_mode": "llm_revisor",
        "llm_role": llm_role,
        "output_policy": "draft_and_qa_only_no_final_write",
    }
    qa_path.write_text(
        json.dumps(result, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run bounded LLM revisor pass for the 8 final memo narratives.")
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--only-direction")
    parser.add_argument("--only-depth")
    parser.add_argument("--llm-role", default="russian_revisor")
    args = parser.parse_args()
    output_dir = (args.output_dir or PROJECT_ROOT / "07_qa" / f"memo_llm_revisor_{datetime.now().strftime('%Y%m%d_%H%M')}").resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    routing = load_routing()
    results = []
    selected = [
        target
        for target in TARGETS
        if (not args.only_direction or target.direction == args.only_direction)
        and (not args.only_depth or target.depth == args.only_depth)
    ]
    for target in selected:
        try:
            result = revise_target(target, output_dir, routing, args.llm_role)
        except OllamaUnavailable as exc:
            result = {
                "direction": target.direction,
                "depth": target.depth,
                "authoring_mode": "llm_revisor",
                "text_qa_status": "blocked_runtime",
                "error": str(exc),
            }
        results.append(result)
        print(target.direction, target.depth, result.get("text_qa_status"), result.get("final_model_metadata", {}).get("final_model"))
    summary = output_dir / "llm_revisor_summary.json"
    summary.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"summary_path {summary}")


if __name__ == "__main__":
    main()
