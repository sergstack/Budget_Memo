from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

try:
    from src.progress import log_progress
except ImportError:  # pragma: no cover
    from progress import log_progress


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "01_raw"
STAGE_DIR = PROJECT_ROOT / "02_stage"
MARTS_DIR = PROJECT_ROOT / "03_marts"
CHARTS_DIR = PROJECT_ROOT / "04_charts"
REPORTS_DIR = PROJECT_ROOT / "06_reports"
QA_DIR = PROJECT_ROOT / "07_qa"

CONTRACT_MD = REPORTS_DIR / "executive_yoy_mom_report_contract.md"
CONTRACT_JSON = REPORTS_DIR / "executive_yoy_mom_report_contract.json"
SECTION_MAP_XLSX = REPORTS_DIR / "executive_yoy_mom_section_map.xlsx"
CLAIM_PLAN_XLSX = REPORTS_DIR / "executive_yoy_mom_claim_plan.xlsx"
CHART_PLACEMENT_XLSX = REPORTS_DIR / "executive_yoy_mom_chart_placement.xlsx"
QA_REPORT = QA_DIR / "report_contract_qa.json"
QA_SUMMARY = QA_DIR / "report_contract_qa_summary.md"

MEMO_PROFILE = "executive_yoy_mom_budget_memo"
MEMO_PROFILE_RU = "Управленческая записка YoY/MoM по бюджету"
DEPTH_MODE = "depth_2_management_memo"
CONTOURS = {"historical_fact_contour", "planning_risk_contour", "qa_contour", "executive_summary"}

REQUIRED_INPUTS = [
    MARTS_DIR / "mart_main_full_budget.parquet",
    MARTS_DIR / "mart_flow_base_month.parquet",
    MARTS_DIR / "mart_signal_catalog_full.parquet",
    MARTS_DIR / "mart_main_compact_executive_yoy_mom.parquet",
    MARTS_DIR / "memo_profile_catalog.parquet",
    MARTS_DIR / "profile_readiness_matrix.parquet",
    MARTS_DIR / "profile_preview_index.parquet",
    CHARTS_DIR / "chart_catalog.parquet",
    QA_DIR / "mart_rebuild_qa_report.json",
    QA_DIR / "chart_qa" / "chart_qa_report.json",
]

DEPTH_MODE_CATALOG = MARTS_DIR / "memo_depth_mode_catalog.parquet"

SECTION_COLUMNS_RU = {
    "section_id": "ID раздела",
    "section_order": "Порядок",
    "section_name_ru": "Название раздела",
    "contour": "Контур",
    "purpose": "Цель",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "source_chart_ids": "ID графиков",
    "required_metrics": "Обязательные метрики",
    "allowed_claim_types": "Разрешённые типы утверждений",
    "forbidden_claims": "Запрещённые утверждения",
    "evidence_requirement": "Требование к evidence",
    "limitation_requirement": "Требование к ограничениям",
    "output_style": "Стиль вывода",
    "max_length_guidance": "Ограничение длины",
}

CLAIM_COLUMNS_RU = {
    "claim_id": "ID claim",
    "section_id": "ID раздела",
    "claim_category": "Категория claim",
    "claim_purpose": "Назначение claim",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "metric": "Метрика",
    "period": "Период",
    "evidence_id_requirement": "Требование evidence_id",
    "qa_status_requirement": "Требование QA статуса",
    "risk_basis_requirement": "Требование risk_basis",
    "confidence_rule": "Правило confidence",
    "forbidden_claims": "Запрещённые утверждения",
    "output_constraint": "Ограничение вывода",
}

CHART_COLUMNS_RU = {
    "chart_order": "Порядок графика",
    "chart_id": "ID графика",
    "chart_name_ru": "Название графика",
    "section_id": "ID раздела",
    "section_name_ru": "Раздел записки",
    "chart_role": "Роль графика",
    "include_in_memo": "Включать в записку",
    "recommended_placement": "Рекомендуемое место",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "metric": "Метрика",
    "grain": "Grain",
    "period": "Период",
    "caption_ru": "Подпись",
    "limitation": "Ограничение",
    "qa_status": "QA статус",
    "image_path": "Путь к изображению",
}


def pipe(values: list[str]) -> str:
    return " | ".join(values)


def snapshot(path: Path) -> dict[str, tuple[int, int]]:
    if not path.exists():
        return {}
    return {
        str(item.relative_to(PROJECT_ROOT)): (item.stat().st_mtime_ns, item.stat().st_size)
        for item in path.rglob("*")
        if item.is_file()
    }


def snapshot_file(path: Path) -> dict[str, tuple[int, int]]:
    if not path.exists():
        return {}
    stat = path.stat()
    return {str(path.relative_to(PROJECT_ROOT)): (stat.st_mtime_ns, stat.st_size)}


def docx_snapshot() -> dict[str, tuple[int, int]]:
    return {
        str(item.relative_to(PROJECT_ROOT)): (item.stat().st_mtime_ns, item.stat().st_size)
        for item in REPORTS_DIR.rglob("*.docx")
    } if REPORTS_DIR.exists() else {}


def base_section(
    section_id: str,
    order: int,
    name: str,
    contour: str,
    purpose: str,
    source_mart: str,
    source_slice: str,
    source_chart_ids: list[str],
    metrics: list[str],
    allowed: list[str],
    forbidden: list[str],
    evidence: str,
    limitation: str,
    style: str,
    length: str,
) -> dict[str, Any]:
    return {
        "section_id": section_id,
        "section_order": order,
        "section_name_ru": name,
        "contour": contour,
        "purpose": purpose,
        "source_mart": source_mart,
        "source_slice": source_slice,
        "source_chart_ids": pipe(source_chart_ids),
        "required_metrics": pipe(metrics),
        "allowed_claim_types": pipe(allowed),
        "forbidden_claims": pipe(forbidden),
        "evidence_requirement": evidence,
        "limitation_requirement": limitation,
        "output_style": style,
        "max_length_guidance": length,
    }


def build_sections() -> pd.DataFrame:
    common_evidence = "Every key claim must reference source_mart, source_slice, metric, period, evidence_id, qa_status."
    common_limit = "Limitations must be visible in section text before any appendix reference."
    return pd.DataFrame(
        [
            base_section(
                "SEC_01_FRAME",
                1,
                "Рамка анализа",
                "executive_summary",
                "Explain period, source, scope, historical/planning split, and limitations.",
                "memo_profile_catalog | profile_readiness_matrix | mart_rebuild_qa_report",
                "not_applicable",
                [],
                ["profile_status", "readiness_status", "qa_status"],
                ["DATA FACT", "LIMITATION"],
                ["production readiness claim", "unsupported scope expansion"],
                common_evidence,
                common_limit,
                "Concise scope frame; no findings narrative.",
                "150-220 words",
            ),
            base_section(
                "SEC_02_EXEC_SUMMARY",
                2,
                "Executive Summary",
                "executive_summary",
                "Summarize top signals by scale, YoY, MoM, localization, planning risk and IN context.",
                "mart_main_compact_executive_yoy_mom | mart_signal_catalog_full",
                "mart_main_compact_executive_yoy_mom",
                [],
                ["headline_metric_eur", "headline_metric_pct", "risk_basis", "confidence_level"],
                ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "RECOMMENDATION", "LIMITATION"],
                ["claim without evidence_id", "low confidence as final fact", "risk without risk_basis"],
                common_evidence + " Compact signals must retain evidence_id.",
                common_limit,
                "Short executive bullets; numbers before adjectives; EUR before percentages.",
                "5-7 bullets, max 350 words",
            ),
            base_section(
                "SEC_03_READING_ROUTE",
                3,
                "Как читать записку",
                "executive_summary",
                "Explain reading route: Масштаб → YoY → MoM → Локализация → Плановый риск → IN context → QC.",
                "report_contract",
                "not_applicable",
                [],
                ["section_order"],
                ["DATA FACT"],
                ["new analytical conclusion"],
                "Reference this report contract and chart placement plan.",
                "No evidence appendix substitution.",
                "Route explanation only.",
                "80-140 words",
            ),
            base_section(
                "SEC_04_PLAN_FACT",
                4,
                "Исторический факт: масштаб Plan-Fact",
                "historical_fact_contour",
                "Show largest budget deviations by amount.",
                "mart_main_full_budget",
                "slice_plan_fact_article_cfo",
                ["CH_EXEC_001_PLAN_FACT_TOP_ABS"],
                ["План, EUR", "Факт, EUR", "Отклонение План-Факт, EUR", "ABS отклонение, EUR", "Исполнение, %", "Отклонение к IN, %"],
                ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "LIMITATION"],
                ["root cause", "overrun/saving without rule", "service flow row as expense"],
                common_evidence,
                "Service rows IN / OUT / IN-OUT must be excluded from expense deviation claims.",
                "Numbers first, table for dense values, chart reference allowed.",
                "250-400 words plus table",
            ),
            base_section(
                "SEC_05_YOY",
                5,
                "YoY: сдвиг уровня к прошлому году",
                "historical_fact_contour",
                "Show fact level changes versus prior year.",
                "mart_main_full_budget",
                "slice_yoy_article",
                ["CH_EXEC_002_YOY_TOP_SHIFT"],
                ["Текущий факт, EUR", "Факт прошлого года, EUR", "YoY отклонение, EUR", "ABS YoY отклонение, EUR", "YoY, %", "Слабая YoY база", "Нет YoY базы"],
                ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "LIMITATION"],
                ["strong YoY conclusion without prior-year base", "extreme percent without EUR materiality"],
                common_evidence,
                "Weak/no YoY base must be stated before interpretation.",
                "Separate YoY from MoM; EUR before percentages.",
                "220-350 words",
            ),
            base_section(
                "SEC_06_MOM",
                6,
                "MoM: помесячная динамика и нестабильность",
                "historical_fact_contour",
                "Show monthly turbulence and signal type.",
                "mart_main_full_budget",
                "slice_mom_article",
                ["CH_EXEC_003_MOM_INSTABILITY"],
                ["MoM отклонение, EUR", "ABS MoM отклонение, EUR", "Тип MoM сигнала", "MoM отклонение к IN, %"],
                ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "LIMITATION"],
                ["mix YoY and MoM in one conclusion", "confirmed cause"],
                common_evidence,
                "MoM signal type is classification, not root cause.",
                "Short paragraphs and chart reference.",
                "200-320 words",
            ),
            base_section(
                "SEC_07_LOCALIZATION",
                7,
                "Локализация: статья × ЦФО",
                "historical_fact_contour",
                "Show where the signal sits and who to ask.",
                "mart_main_full_budget",
                "slice_localization_article_cfo",
                ["CH_EXEC_004_LOCALIZATION_ARTICLE_CFO"],
                ["Статья", "ЦФО", "ABS отклонение ЦФО, EUR", "Доля ЦФО в отклонении статьи, %", "Тип концентрации", "Кандидат владельца"],
                ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "RECOMMENDATION", "LIMITATION"],
                ["confirmed owner action without owner/due/status", "confirmed root cause"],
                common_evidence,
                "Owner is candidate until confirmed.",
                "Action-oriented but evidence-bounded.",
                "250-350 words",
            ),
            base_section(
                "SEC_08_PLANNING_RISK",
                8,
                "Плановый риск: план к исторической базе",
                "planning_risk_contour",
                "Show future planning risk versus historical base.",
                "mart_main_full_budget",
                "slice_plan_vs_history_article_cfo",
                ["CH_EXEC_005_PLANNING_RISK"],
                ["План планового периода, EUR", "Историческая база, EUR", "План к базе, EUR", "ABS план к базе, EUR", "План к базе, %", "Месяцев базы", "Месяцев без базы"],
                ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "LIMITATION", "HYPOTHESIS"],
                ["actual execution conclusion", "overrun", "saving"],
                common_evidence,
                "Must say future budget risk, not actual execution.",
                "Clearly separate planning contour from historical fact.",
                "250-380 words",
            ),
            base_section(
                "SEC_09_IN_CONTEXT",
                9,
                "iGaming flow context: отклонения к IN",
                "historical_fact_contour",
                "Explain proportionality to inflow and flow base context.",
                "mart_flow_base_month | mart_main_full_budget",
                "mart_flow_base_month | slice_plan_fact_article_cfo",
                ["CH_EXEC_006_IN_CONTEXT", "CH_EXEC_007_FLOW_BASE"],
                ["IN, EUR", "OUT, EUR", "IN-OUT, EUR", "OUT к IN, %", "IN-OUT маржа, %", "Отклонение к IN, %"],
                ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "LIMITATION"],
                ["IN-OUT summed across ordinary article rows", "ratio without valid denominator"],
                common_evidence,
                "Denominator status must be valid; explain IN as denominator.",
                "Explain proportionality; no causal claim.",
                "220-350 words",
            ),
            base_section(
                "SEC_10_QC_LIMITATIONS",
                10,
                "QC и ограничения",
                "qa_contour",
                "Show what limits interpretation.",
                "profile_readiness_matrix | chart_qa_report | mart_signal_catalog_full",
                "slice_source_mix_summary",
                ["CH_EXEC_008_QA_LIMITATIONS"],
                ["qa_status", "readiness_status", "source_mix", "rows_count"],
                ["DATA FACT", "LIMITATION"],
                ["DQ issue as financial misstatement", "appendix replacing executive memo"],
                common_evidence,
                "DQ fail blocks management conclusion unless explicitly limited.",
                "Limitations visible before appendix.",
                "180-300 words",
            ),
            base_section(
                "SEC_11_ACTION_REGISTER",
                11,
                "Реестр приоритетных проверок",
                "qa_contour",
                "List priority checks and candidate owners.",
                "mart_signal_catalog_full | mart_main_compact_executive_yoy_mom",
                "mart_signal_catalog_full",
                [],
                ["Объект", "Тип сигнала", "Что проверить", "Owner / candidate owner", "Срок", "Приоритет", "Evidence ID"],
                ["DATA FACT", "RECOMMENDATION", "LIMITATION", "HYPOTHESIS"],
                ["action without owner/due/status as final action"],
                common_evidence,
                "Action is valid only with owner, due date, and status; otherwise candidate action.",
                "Table-first, concise.",
                "Table plus 80-120 words",
            ),
            base_section(
                "SEC_12_FINAL_CONCLUSION",
                12,
                "Итоговый вывод",
                "executive_summary",
                "Summarize supported conclusions and next actions.",
                "mart_main_compact_executive_yoy_mom | mart_signal_catalog_full",
                "mart_main_compact_executive_yoy_mom",
                [],
                ["headline_metric_eur", "risk_basis", "confidence_level", "owner_candidate"],
                ["INTERPRETATION", "RECOMMENDATION", "LIMITATION"],
                ["unsupported claim", "production readiness", "evidence appendix as memo"],
                common_evidence,
                "Only supported conclusions; limitations must remain visible.",
                "Concise executive close, no decorative language.",
                "120-220 words",
            ),
        ]
    )


def build_claim_plan(sections: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    claim_templates = [
        ("DATA FACT", "State observed value from source."),
        ("CALCULATION RESULT", "State deterministic metric or ranking."),
        ("INTERPRETATION", "Explain bounded meaning without causality leap."),
        ("LIMITATION", "State caveat or blocker."),
    ]
    extra_by_section = {
        "SEC_07_LOCALIZATION": [("RECOMMENDATION", "Route question to candidate owner.")],
        "SEC_08_PLANNING_RISK": [("HYPOTHESIS", "Mark future planning risk hypothesis explicitly.")],
        "SEC_11_ACTION_REGISTER": [("RECOMMENDATION", "Create candidate verification action.")],
        "SEC_12_FINAL_CONCLUSION": [("RECOMMENDATION", "Summarize next action only if owner/due/status exists.")],
    }
    for section in sections.to_dict("records"):
        allowed = set(section["allowed_claim_types"].split(" | "))
        for category, purpose in [*claim_templates, *extra_by_section.get(section["section_id"], [])]:
            if category not in allowed:
                continue
            rows.append(
                {
                    "claim_id": f"{section['section_id']}_{category.replace(' ', '_')}",
                    "section_id": section["section_id"],
                    "claim_category": category,
                    "claim_purpose": purpose,
                    "source_mart": section["source_mart"],
                    "source_slice": section["source_slice"],
                    "metric": section["required_metrics"],
                    "period": "Must match source period field or documented all_available_periods.",
                    "evidence_id_requirement": "Required for every key claim; must trace to signal/catalog/chart data where applicable.",
                    "qa_status_requirement": "qa_status must be pass or limitation must be explicit.",
                    "risk_basis_requirement": "Required for risk claims; risk without risk_basis is forbidden.",
                    "confidence_rule": "Low confidence cannot be final fact; write as limitation or hypothesis.",
                    "forbidden_claims": section["forbidden_claims"],
                    "output_constraint": "No final prose in this contract; future memo must stay concise and evidence-bounded.",
                }
            )
    return pd.DataFrame(rows)


def build_chart_placement(sections: pd.DataFrame, chart_catalog: pd.DataFrame) -> pd.DataFrame:
    section_by_chart: dict[str, dict[str, Any]] = {}
    for section in sections.to_dict("records"):
        for chart_id in section["source_chart_ids"].split(" | "):
            if chart_id:
                section_by_chart[chart_id] = section
    rows = []
    for chart in chart_catalog.sort_values("chart_order").to_dict("records"):
        section = section_by_chart.get(chart["chart_id"], {})
        rows.append(
            {
                "chart_order": int(chart["chart_order"]),
                "chart_id": chart["chart_id"],
                "chart_name_ru": chart["chart_name_ru"],
                "section_id": section.get("section_id", "APPENDIX"),
                "section_name_ru": section.get("section_name_ru", chart["memo_section"]),
                "chart_role": chart["chart_role"],
                "include_in_memo": bool(chart["include_in_memo"]),
                "recommended_placement": chart["recommended_placement"],
                "source_mart": chart["source_mart"],
                "source_slice": chart["source_slice"],
                "metric": chart["metric"],
                "grain": chart["grain"],
                "period": chart["period"],
                "caption_ru": chart["caption_ru"],
                "limitation": chart["limitation"],
                "qa_status": chart["qa_status"],
                "image_path": chart["image_path"],
            }
        )
    return pd.DataFrame(rows)


def write_excel(path: Path, sheet_name: str, data: pd.DataFrame, columns: dict[str, str]) -> None:
    visible = data[list(columns)].rename(columns=columns)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        visible.to_excel(writer, sheet_name=sheet_name, index=False)
        ws = writer.book[sheet_name]
        ws.freeze_panes = "A2"
        for cells in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in cells[:80])
            ws.column_dimensions[cells[0].column_letter].width = min(max(max_len + 2, 12), 60)


def build_contract_payload(sections: pd.DataFrame, claim_plan: pd.DataFrame, chart_placement: pd.DataFrame) -> dict[str, Any]:
    depth_modes = pd.read_parquet(DEPTH_MODE_CATALOG).to_dict(orient="records") if DEPTH_MODE_CATALOG.exists() else []
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "memo_profile_ru": MEMO_PROFILE_RU,
        "default_depth_mode": "depth_2_management_memo",
        "allowed_depth_modes": [
            "depth_1_executive_brief",
            "depth_2_management_memo",
            "depth_3_finance_working_package",
            "depth_4_operating_model",
        ],
        "depth_mode_catalog": depth_modes,
        "mode": "report_contract_only_no_docx_no_final_prose",
        "contours": ["historical_fact_contour", "planning_risk_contour"],
        "supporting_contours": ["qa_contour", "executive_summary"],
        "required_output_style": {
            "style": "concise executive memo",
            "rules": [
                "numbers before adjectives",
                "EUR before percentages",
                "short paragraphs",
                "no decorative language",
                "no unsupported claims",
                "tables where numbers are dense",
                "limitations visible before appendix",
            ],
        },
        "global_claim_rules": [
            "Every key claim references source_mart, source_slice, metric, period, evidence_id, qa_status.",
            "Planning risk is future budget risk, not actual execution.",
            "YoY and MoM are separate sections.",
            "Extreme percentages are not main conclusions without EUR materiality.",
            "IN context explains proportionality to inflow.",
            "IN-OUT is not summed across ordinary article rows.",
            "Risk must have risk_basis.",
            "Low confidence must not be written as final fact.",
            "Timing candidates must not be called confirmed timing.",
            "Evidence appendix must not replace executive memo.",
        ],
        "claim_categories": ["DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "RECOMMENDATION", "LIMITATION", "HYPOTHESIS"],
        "sections": sections.to_dict(orient="records"),
        "claim_plan": claim_plan.to_dict(orient="records"),
        "chart_placement": chart_placement.to_dict(orient="records"),
    }


def write_markdown(payload: dict[str, Any], sections: pd.DataFrame, chart_placement: pd.DataFrame) -> None:
    lines = [
        f"# {payload['memo_profile_ru']} — report/DOCX contract",
        "",
        "Mode: report contract only. Do not generate final DOCX or final memo prose from this file.",
        "",
        "Default depth mode: `depth_2_management_memo`.",
        "Allowed depth modes: `depth_1_executive_brief`, `depth_2_management_memo`, `depth_3_finance_working_package`, `depth_4_operating_model`.",
        "",
        "## Memo Contours",
        "- historical_fact_contour",
        "- planning_risk_contour",
        "- qa_contour",
        "- executive_summary",
        "",
        "## Global Claim Rules",
        *[f"- {rule}" for rule in payload["global_claim_rules"]],
        "",
        "## Section Map",
    ]
    for section in sections.sort_values("section_order").to_dict("records"):
        lines.extend(
            [
                "",
                f"### {section['section_order']}. {section['section_name_ru']}",
                f"- section_id: `{section['section_id']}`",
                f"- contour: `{section['contour']}`",
                f"- purpose: {section['purpose']}",
                f"- source_mart: `{section['source_mart']}`",
                f"- source_slice: `{section['source_slice']}`",
                f"- source_chart_ids: `{section['source_chart_ids'] or 'none'}`",
                f"- required_metrics: {section['required_metrics']}",
                f"- allowed_claim_types: {section['allowed_claim_types']}",
                f"- forbidden_claims: {section['forbidden_claims']}",
                f"- evidence_requirement: {section['evidence_requirement']}",
                f"- limitation_requirement: {section['limitation_requirement']}",
                f"- output_style: {section['output_style']}",
                f"- max_length_guidance: {section['max_length_guidance']}",
            ]
        )
    lines.extend(["", "## Chart Placement"])
    for row in chart_placement.sort_values("chart_order").to_dict("records"):
        lines.append(
            f"- {row['chart_order']}. `{row['chart_id']}` → {row['section_name_ru']} "
            f"({row['chart_role']}, include={row['include_in_memo']}): {row['caption_ru']}"
        )
    CONTRACT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_contract(
    sections: pd.DataFrame,
    claim_plan: pd.DataFrame,
    chart_placement: pd.DataFrame,
    raw_before: dict[str, tuple[int, int]],
    stage_before: dict[str, tuple[int, int]],
    marts_before: dict[str, tuple[int, int]],
    charts_before: dict[str, tuple[int, int]],
    docx_before: dict[str, tuple[int, int]],
) -> dict[str, Any]:
    raw_after = snapshot(RAW_DIR)
    stage_after = snapshot(STAGE_DIR)
    marts_after = snapshot(MARTS_DIR)
    charts_after = snapshot(CHARTS_DIR)
    docx_after = docx_snapshot()
    chart_catalog = pd.read_parquet(CHARTS_DIR / "chart_catalog.parquet")
    expected_sections = [
        "Рамка анализа",
        "Executive Summary",
        "Как читать записку",
        "Исторический факт: масштаб Plan-Fact",
        "YoY: сдвиг уровня к прошлому году",
        "MoM: помесячная динамика и нестабильность",
        "Локализация: статья × ЦФО",
        "Плановый риск: план к исторической базе",
        "iGaming flow context: отклонения к IN",
        "QC и ограничения",
        "Реестр приоритетных проверок",
        "Итоговый вывод",
    ]
    checks = {
        "report_contract_exists_md_json": CONTRACT_MD.exists() and CONTRACT_JSON.exists(),
        "all_12_sections_exist": len(sections) == 12 and sections["section_name_ru"].tolist() == expected_sections,
        "section_order_correct": sections["section_order"].tolist() == list(range(1, 13)),
        "each_section_has_source_or_documented_reason": sections["source_mart"].fillna("").ne("").all()
        and sections["source_slice"].fillna("").ne("").all(),
        "each_section_has_evidence_requirement": sections["evidence_requirement"].fillna("").ne("").all(),
        "each_section_has_limitation_rule": sections["limitation_requirement"].fillna("").ne("").all(),
        "section_contours_valid": set(sections["contour"]).issubset(CONTOURS),
        "chart_placement_file_exists": CHART_PLACEMENT_XLSX.exists(),
        "claims_plan_exists": CLAIM_PLAN_XLSX.exists() and not claim_plan.empty,
        "chart_placement_matches_accepted_catalog": set(chart_placement["chart_id"]) == set(chart_catalog["chart_id"]),
        "executive_body_charts_1_8": chart_placement.loc[chart_placement["chart_order"].le(8), "chart_role"].eq("executive_body").all(),
        "appendix_charts_9_10": chart_placement.loc[chart_placement["chart_order"].ge(9), "chart_role"].eq("appendix").all(),
        "chart_metadata_preserved": chart_placement[["source_mart", "source_slice", "metric", "grain", "period", "caption_ru", "limitation"]]
        .fillna("")
        .ne("")
        .all()
        .all(),
        "no_old_final_memo_structure_used": not CONTRACT_MD.read_text(encoding="utf-8").lower().count("plan_base_risk_memo"),
        "planning_risk_marked_future_not_execution": sections.loc[
            sections["section_id"].eq("SEC_08_PLANNING_RISK"), "forbidden_claims"
        ].str.contains("actual execution", regex=False).all(),
        "yoy_and_mom_separate_sections": bool(
            sections.loc[sections["section_id"].eq("SEC_05_YOY"), "section_name_ru"].iloc[0].startswith("YoY")
            and sections.loc[sections["section_id"].eq("SEC_06_MOM"), "section_name_ru"].iloc[0].startswith("MoM")
        ),
        "in_context_included": sections["section_id"].eq("SEC_09_IN_CONTEXT").any(),
        "required_claim_categories_present": {"DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "RECOMMENDATION", "LIMITATION", "HYPOTHESIS"}.issubset(
            set(claim_plan["claim_category"])
        ),
        "raw_untouched": raw_before == raw_after,
        "stage_untouched": stage_before == stage_after,
        "mart_formulas_untouched": marts_before == marts_after,
        "chart_data_untouched": charts_before == charts_after,
        "no_docx_generated_or_modified": docx_before == docx_after,
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "pass" if all(bool(value) for value in checks.values()) else "fail",
        "memo_profile": MEMO_PROFILE,
        "checks": {key: bool(value) for key, value in checks.items()},
        "section_count": int(len(sections)),
        "claim_plan_rows": int(len(claim_plan)),
        "chart_placement_rows": int(len(chart_placement)),
        "production_readiness_claimed": False,
    }


def main() -> None:
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="report_contract_generation", status="start")
    raw_before = snapshot(RAW_DIR)
    stage_before = snapshot(STAGE_DIR)
    marts_before = snapshot(MARTS_DIR)
    charts_before = snapshot(CHARTS_DIR)
    docx_before = docx_snapshot()
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_INPUTS if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing accepted sources: {missing}")

    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="section_claim_chart_contracts", status="start")
    sections = build_sections()
    claim_plan = build_claim_plan(sections)
    chart_catalog = pd.read_parquet(CHARTS_DIR / "chart_catalog.parquet")
    chart_placement = build_chart_placement(sections, chart_catalog)
    payload = build_contract_payload(sections, claim_plan, chart_placement)
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="section_claim_chart_contracts", status="done", details={"sections": len(sections), "claim_rows": len(claim_plan)})

    CONTRACT_JSON.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(payload, sections, chart_placement)
    write_excel(SECTION_MAP_XLSX, "Карта_Разделов", sections, SECTION_COLUMNS_RU)
    write_excel(CLAIM_PLAN_XLSX, "План_Claim", claim_plan, CLAIM_COLUMNS_RU)
    write_excel(CHART_PLACEMENT_XLSX, "Размещение_Графиков", chart_placement, CHART_COLUMNS_RU)

    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="report_contract_qa", status="start")
    qa = validate_contract(sections, claim_plan, chart_placement, raw_before, stage_before, marts_before, charts_before, docx_before)
    QA_REPORT.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QA_SUMMARY.write_text(
        "\n".join(
            [
                "# Report Contract QA Summary",
                "",
                f"qa_status: {qa['qa_status']}",
                f"memo_profile: {MEMO_PROFILE}",
                f"section_count: {qa['section_count']}",
                f"claim_plan_rows: {qa['claim_plan_rows']}",
                f"chart_placement_rows: {qa['chart_placement_rows']}",
                "",
                "## Checks",
                *[f"- {key}: {'pass' if value else 'fail'}" for key, value in qa["checks"].items()],
                "",
                "## Residual Risks",
                "- This is a contract only; no final DOCX or final prose was generated.",
                "- Future memo generation must still ground every claim to evidence_id and QA status.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="report_contract_generation", status=qa["qa_status"], details={"sections": qa["section_count"]})
    print(json.dumps({"qa_status": qa["qa_status"], "section_count": qa["section_count"], "checks": qa["checks"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
