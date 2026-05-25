from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "01_raw"
STAGE_DIR = PROJECT_ROOT / "02_stage"
MARTS_DIR = PROJECT_ROOT / "03_marts"
QA_DIR = PROJECT_ROOT / "07_qa"
REPORTS_DIR = PROJECT_ROOT / "06_reports"

MART_SIGNAL_CATALOG = MARTS_DIR / "mart_signal_catalog_full.parquet"
MART_COMPACT = MARTS_DIR / "mart_main_compact_executive_yoy_mom.parquet"
MART_MAIN_FULL = MARTS_DIR / "mart_main_full_budget.parquet"
MART_FLOW = MARTS_DIR / "mart_flow_base_month.parquet"
BUILD_MARTS_SCRIPT = PROJECT_ROOT / "src" / "build_marts.py"

PROFILE_CATALOG_PARQUET = MARTS_DIR / "memo_profile_catalog.parquet"
PROFILE_CATALOG_XLSX = MARTS_DIR / "memo_profile_catalog.xlsx"
READINESS_PARQUET = MARTS_DIR / "profile_readiness_matrix.parquet"
READINESS_XLSX = MARTS_DIR / "profile_readiness_matrix.xlsx"
PREVIEW_PARQUET = MARTS_DIR / "profile_preview_index.parquet"
PREVIEW_XLSX = MARTS_DIR / "profile_preview_index.xlsx"
DEPTH_MODE_PARQUET = MARTS_DIR / "memo_depth_mode_catalog.parquet"
DEPTH_MODE_XLSX = MARTS_DIR / "memo_depth_mode_catalog.xlsx"
QA_REPORT = QA_DIR / "memo_profile_catalog_qa_report.json"
QA_SUMMARY = QA_DIR / "memo_profile_catalog_qa_summary.md"
DEPTH_QA_REPORT = QA_DIR / "depth_modes_qa.json"
DEPTH_QA_SUMMARY = QA_DIR / "depth_modes_qa_summary.md"
DEPTH_TEMPLATE_MD = REPORTS_DIR / "99_templates" / "depth_modes.md"

PROFILE_SIGNAL_FIELDS = [
    "eligible_memo_profiles",
    "primary_memo_profile",
    "memo_section",
    "profile_priority",
    "release_priority",
    "profile_readiness_status",
]

CATALOG_EXCEL_COLUMNS = {
    "profile_code": "Код профиля",
    "profile_ru_name": "Название записки",
    "release_priority": "Приоритет релиза",
    "profile_status": "Статус профиля",
    "audience": "Аудитория",
    "period_logic": "Период",
    "main_question": "Главный вопрос",
    "required_sections": "Обязательные разделы",
    "source_signal_types": "Типы сигналов",
    "source_marts": "Источники MART",
    "source_slices": "Источники срезов",
    "compact_mart_name": "Compact MART",
    "block_status": "Статус блока",
    "output_layer": "Слой вывода",
    "publish_rule": "Правило публикации",
    "readiness_rules": "Правила готовности",
    "stop_conditions": "Stop conditions",
    "acceptance_criteria": "Acceptance criteria",
    "evidence_requirement": "Требование к evidence",
    "confidence_rule": "Правило confidence",
    "action_requirement": "Требование к action",
    "default_depth_mode": "Режим глубины по умолчанию",
    "allowed_depth_modes": "Разрешённые режимы глубины",
    "limitations": "Ограничения",
}

READINESS_EXCEL_COLUMNS = {
    "profile_code": "Код профиля",
    "profile_ru_name": "Название записки",
    "eligible_signal_count": "Количество подходящих сигналов",
    "high_risk_signal_count": "Количество high-risk сигналов",
    "qc_blocker_signal_count": "Количество QC/blocker сигналов",
    "data_readiness": "Готовность данных",
    "readiness_status": "Статус готовности",
    "limitation_reason": "Причина ограничения",
    "recommendation": "Рекомендация",
    "next_action": "Следующее действие",
    "default_depth_mode": "Режим глубины по умолчанию",
    "ready_depth_modes": "Готовые режимы глубины",
    "partial_depth_modes": "Частичные режимы глубины",
    "blocked_depth_modes": "Заблокированные режимы глубины",
    "depth_mode_readiness": "Готовность по режимам глубины",
}

DEPTH_MODE_EXCEL_COLUMNS = {
    "depth_mode": "Код режима глубины",
    "depth_mode_ru_name": "Название режима глубины",
    "depth_mode_status": "Статус режима глубины",
    "audience": "Аудитория",
    "purpose": "Назначение",
    "included_sections": "Включённые разделы",
    "excluded_sections": "Исключённые разделы",
    "chart_policy": "Политика графиков",
    "evidence_policy": "Политика evidence",
    "appendix_policy": "Политика appendix",
    "action_policy": "Политика action",
    "output_artifact_policy": "Политика output artifacts",
    "stop_conditions": "Стоп-условия",
    "acceptance_criteria": "Критерии приемки",
}

PREVIEW_EXCEL_COLUMNS = {
    "profile_code": "Код профиля",
    "profile_ru_name": "Название записки",
    "top_5_signals": "Топ-5 сигналов",
    "fillable_sections": "Разделы, которые можно заполнить",
    "missing_sections": "Разделы, где данных не хватает",
    "main_limitations": "Основные ограничения",
    "can_build_docx": "Можно ли строить DOCX: да/нет",
}

RELEASE_RANK = {"R1": 1, "R2": 2, "R3": 3}
QC_SIGNAL_TYPES = {"counterparty_quality", "source_quality", "currency_exposure"}


def pipe(values: list[str]) -> str:
    return " | ".join(values)


def define_depth_modes() -> pd.DataFrame:
    modes = [
        {
            "depth_mode": "depth_1_executive_brief",
            "depth_mode_ru_name": "Короткая executive-версия",
            "depth_mode_status": "active",
            "audience": "CEO / CFO / COO",
            "purpose": "5-7 key conclusions, key risks, decisions needed, visible limitations.",
            "included_sections": pipe(["Executive Summary", "key numbers table", "3-5 charts max", "top actions", "limitations"]),
            "excluded_sections": pipe(["detailed evidence tables", "full DQ logs", "full slice tables", "full appendix"]),
            "chart_policy": "Use 3-5 executive charts max; no appendix charts unless explicitly approved.",
            "evidence_policy": "Compact evidence references only; technical IDs stay in appendix/evidence if used.",
            "appendix_policy": "No full appendix by default.",
            "action_policy": "Actions shown only when owner / due date / status are available or clearly marked as candidate.",
            "output_artifact_policy": "Short MD/DOCX executive brief; no finance working package tables.",
            "stop_conditions": "DQ Fail blocks management conclusion. Low confidence must not be final fact. Risk requires risk_basis.",
            "acceptance_criteria": "5-7 grounded bullets, visible limitations, 3-5 charts max, no full evidence dump.",
        },
        {
            "depth_mode": "depth_2_management_memo",
            "depth_mode_ru_name": "Стандартная управленческая записка",
            "depth_mode_status": "active",
            "audience": "CFO / COO / руководители",
            "purpose": "Full management memo with route Масштаб → YoY → MoM → Локализация → Плановый риск → IN context → QC.",
            "included_sections": pipe(["all 12 memo sections", "6-8 executive body charts", "compact evidence references", "candidate action register", "limitations"]),
            "excluded_sections": pipe(["full technical evidence dump", "full working package tables"]),
            "chart_policy": "Use accepted executive body charts; appendix charts remain appendix candidates.",
            "evidence_policy": "Compact evidence references in body; detailed evidence stays in appendix/evidence layer.",
            "appendix_policy": "Appendix allowed but clearly separated from executive body.",
            "action_policy": "Candidate action register allowed; owner / due date / status required for final action.",
            "output_artifact_policy": "Management MD/DOCX plus compact references; no full slice workbook unless separately requested.",
            "stop_conditions": "DQ Fail blocks management conclusion. Evidence appendix must not replace memo. IN/OUT requires Definition Card.",
            "acceptance_criteria": "All 12 sections present, limitations visible, YoY/MoM separated, planning risk framed as future risk.",
        },
        {
            "depth_mode": "depth_3_finance_working_package",
            "depth_mode_ru_name": "Рабочий finance package",
            "depth_mode_status": "active",
            "audience": "Сергей / Finance Team",
            "purpose": "Full evidence and review package behind the memo.",
            "included_sections": pipe(["all memo slices", "full evidence map", "DQ checks", "timing candidates", "INOUT checks", "baseline / planning risk details", "chart data", "source references", "full slice workbook"]),
            "excluded_sections": pipe(["decorative executive prose"]),
            "chart_policy": "Charts may be included as references; chart data must remain traceable.",
            "evidence_policy": "Full evidence map and source references are included.",
            "appendix_policy": "Appendix / working package is primary output.",
            "action_policy": "Review actions can be tracked as candidates; final action still requires owner / due date / status.",
            "output_artifact_policy": "XLSX/MD/JSON working package; no decorative executive prose.",
            "stop_conditions": "Do not publish as executive conclusion if DQ Fail, weak confidence, or missing risk_basis exists.",
            "acceptance_criteria": "Full slice workbook/evidence present, no raw/stage mutation, no unsupported management conclusions.",
        },
        {
            "depth_mode": "depth_4_operating_model",
            "depth_mode_ru_name": "Operating model / контур управления действиями",
            "depth_mode_status": "active",
            "audience": "Finance PMO / budget owners",
            "purpose": "Manage follow-up after memo.",
            "included_sections": pipe(["action tracker", "owner", "due date", "status", "owner confirmation", "escalation rule", "decision log", "backlog correction", "next review date"]),
            "excluded_sections": pipe(["long narrative memo unless needed"]),
            "chart_policy": "Charts optional; include only if they support owner action or escalation.",
            "evidence_policy": "Evidence required for each action; technical detail stays in source_refs/evidence.",
            "appendix_policy": "Appendix optional and action-focused.",
            "action_policy": "Action is valid only with owner / due date / status; otherwise candidate action.",
            "output_artifact_policy": "Action register, tracker workbook, decision log; narrative memo optional.",
            "stop_conditions": "Actions without owner / due date / status cannot be published as final actions.",
            "acceptance_criteria": "Owner, due date, status, confirmation and escalation rule are present for each final action.",
        },
    ]
    return pd.DataFrame(modes)


def snapshot_tree(path: Path) -> dict[str, tuple[int, int]]:
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


def snapshot_docx(path: Path) -> dict[str, tuple[int, int]]:
    if not path.exists():
        return {}
    return {
        str(item.relative_to(PROJECT_ROOT)): (item.stat().st_mtime_ns, item.stat().st_size)
        for item in path.rglob("*.docx")
        if item.is_file()
    }


def define_profiles() -> pd.DataFrame:
    profiles: list[dict[str, Any]] = [
        {
            "profile_code": "executive_yoy_mom_budget_memo",
            "profile_ru_name": "Управленческая записка YoY/MoM по бюджету",
            "release_priority": "R1",
            "profile_status": "active",
            "audience": "CEO / CFO / COO",
            "period_logic": "Закрытый месяц, YoY, MoM, YTD where available",
            "main_question": "Где масштабные отклонения, устойчивые YoY/MoM сдвиги, локализация ответственности и плановый риск в IN context?",
            "required_sections": pipe(["Executive summary", "Plan-Fact", "YoY", "MoM", "Локализация", "Плановый риск", "IN context", "Ограничения"]),
            "source_signal_types": pipe(["plan_fact_scale", "yoy_shift", "mom_instability", "localization_concentration", "planning_risk", "flow_pressure", "source_quality"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_compact_executive_yoy_mom", "mart_main_full_budget", "mart_flow_base_month"]),
            "source_slices": pipe(["slice_plan_fact_article", "slice_yoy_article", "slice_mom_article", "slice_localization_article_cfo", "slice_planning_risk_candidates"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Ready when R1 profile has plan/fact, YoY or MoM, flow context and traceable signal catalog entries.",
            "stop_conditions": "No reconciliation, missing IN denominator, missing risk_basis, untraceable compact signals.",
            "limitations": "Preview layer only; no DOCX or executive conclusions generated.",
        },
        {
            "profile_code": "monthly_plan_fact_memo",
            "profile_ru_name": "Ежемесячная записка План-Факт",
            "release_priority": "R1",
            "profile_status": "active",
            "audience": "CFO / Finance",
            "period_logic": "Закрытый месяц",
            "main_question": "Как исполнен бюджет за закрытый месяц и где основные план-факт отклонения?",
            "required_sections": pipe(["Plan-Fact", "Топ отклонений", "Контрагенты", "QA limitations"]),
            "source_signal_types": pipe(["plan_fact_scale", "counterparty_quality", "source_quality", "flow_pressure"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget", "mart_flow_base_month"]),
            "source_slices": pipe(["slice_plan_fact_article_month", "slice_plan_fact_counterparty", "slice_counterparty_top_by_delta"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Ready when plan/fact signals and source QA signals are present.",
            "stop_conditions": "No plan/fact mart, reconciliation blocker, service rows in expense deviations.",
            "limitations": "Preview layer only; monthly close approval is outside this artifact.",
        },
        {
            "profile_code": "weekly_coo_cash_cost_memo",
            "profile_ru_name": "Еженедельная COO-записка по ДДС и расходам",
            "release_priority": "R1",
            "profile_status": "active",
            "audience": "COO",
            "period_logic": "Week / MTD candidate from available monthly mart context",
            "main_question": "Что изменилось за неделю или MTD и какие расходы давят на IN?",
            "required_sections": pipe(["MTD/period movement", "Расходы к IN", "MoM context", "Ограничения периода"]),
            "source_signal_types": pipe(["flow_pressure", "plan_fact_scale", "mom_instability"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_flow_base_month", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_mom_article_month", "slice_plan_fact_article_month"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Partial unless weekly grain exists; monthly MART can only support preview.",
            "stop_conditions": "No explicit weekly/MTD grain, missing IN denominator.",
            "limitations": "Current MART is monthly; weekly memo remains preview/partial until weekly source grain is introduced.",
        },
        {
            "profile_code": "planning_risk_memo",
            "profile_ru_name": "Записка по рискам плановой базы",
            "release_priority": "R1",
            "profile_status": "active",
            "audience": "CFO / Budget owners",
            "period_logic": "Budget period vs historical base",
            "main_question": "Где плановая база расходится с историей и требует подтверждения владельца?",
            "required_sections": pipe(["План к базе", "Риски планирования", "Owner route", "Limitations"]),
            "source_signal_types": pipe(["planning_risk", "localization_concentration", "source_quality"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_plan_vs_history_article", "slice_plan_vs_history_article_cfo", "slice_planning_risk_candidates"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Ready when planning_risk signals exist and are separated from actual execution.",
            "stop_conditions": "Planning risk treated as actual execution, missing historical base flags.",
            "limitations": "Requires owner validation before management conclusions.",
        },
        {
            "profile_code": "data_quality_blocker_memo",
            "profile_ru_name": "Записка по блокерам качества данных",
            "release_priority": "R1",
            "profile_status": "active",
            "audience": "Finance / Data owner",
            "period_logic": "Current MART build scope",
            "main_question": "Что блокирует публикацию управленческих выводов?",
            "required_sections": pipe(["Source quality", "Counterparty quality", "Currency quality", "Stop conditions"]),
            "source_signal_types": pipe(["source_quality", "counterparty_quality", "currency_exposure"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_source_mix_summary", "slice_dq_flags", "slice_counterparty_unknown", "slice_currency_exposure"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Ready when QA/source/counterparty/currency signals are traceable.",
            "stop_conditions": "Missing QA source slices, untraceable blocker signals.",
            "limitations": "Identifies blockers only; does not remediate source data.",
        },
        {
            "profile_code": "article_deep_dive_memo",
            "profile_ru_name": "Deep Dive по статье бюджета",
            "release_priority": "R2",
            "profile_status": "planned",
            "audience": "Finance / Owner",
            "period_logic": "Selected article across periods",
            "main_question": "Что объясняет динамику и отклонения конкретной статьи?",
            "required_sections": pipe(["Plan-Fact", "YoY", "MoM", "Контрагенты", "Owner route"]),
            "source_signal_types": pipe(["plan_fact_scale", "yoy_shift", "mom_instability", "planning_risk", "localization_concentration"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_plan_fact_article_month", "slice_yoy_article_month", "slice_mom_article_month"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until article parameter and DOCX template are approved.",
            "stop_conditions": "No selected article, missing source evidence.",
            "limitations": "Profile metadata only; no parameterized deep dive generated.",
        },
        {
            "profile_code": "cfo_owner_localization_memo",
            "profile_ru_name": "Записка по ЦФО / зоне ответственности",
            "release_priority": "R2",
            "profile_status": "planned",
            "audience": "Руководитель ЦФО / CFO",
            "period_logic": "Selected CFO and available months",
            "main_question": "Какие статьи и контрагенты формируют сигнал внутри ЦФО?",
            "required_sections": pipe(["Локализация ЦФО", "Plan-Fact", "Контрагенты", "Действия владельца"]),
            "source_signal_types": pipe(["localization_concentration", "plan_fact_scale", "planning_risk", "counterparty_quality"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_localization_article_cfo", "slice_localization_owner_route", "slice_plan_fact_article_cfo"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until CFO parameter and owner workflow are approved.",
            "stop_conditions": "Missing CFO field or owner route.",
            "limitations": "No owner workflow side effects are generated.",
        },
        {
            "profile_code": "counterparty_quality_memo",
            "profile_ru_name": "Записка по качеству контрагентов",
            "release_priority": "R2",
            "profile_status": "planned",
            "audience": "Finance / Data owner",
            "period_logic": "Current MART build scope",
            "main_question": "Где unknown, missing key и mapping quality ограничивают выводы?",
            "required_sections": pipe(["Unknown counterparties", "Missing keys", "Concentration", "Limitations"]),
            "source_signal_types": pipe(["counterparty_quality", "source_quality"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_counterparty_unknown", "slice_counterparty_missing_key", "slice_counterparty_concentration"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until data-owner remediation workflow is approved.",
            "stop_conditions": "No counterparty quality slices.",
            "limitations": "No source corrections are performed.",
        },
        {
            "profile_code": "quarterly_budget_dynamics_review",
            "profile_ru_name": "Квартальный обзор бюджетной динамики",
            "release_priority": "R2",
            "profile_status": "planned",
            "audience": "CFO / CEO",
            "period_logic": "Quarter / YTD from monthly MART",
            "main_question": "Какие устойчивые тренды за квартал и YTD видны в бюджете?",
            "required_sections": pipe(["Quarter trend", "YTD", "YoY", "MoM", "Plan-Fact"]),
            "source_signal_types": pipe(["yoy_shift", "mom_instability", "plan_fact_scale", "flow_pressure"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget", "mart_flow_base_month"]),
            "source_slices": pipe(["slice_yoy_article_month", "slice_mom_article_month", "slice_plan_fact_article_month"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until quarter/YTD aggregation contract is approved.",
            "stop_conditions": "Insufficient monthly coverage for quarter.",
            "limitations": "Current profile does not create new quarter formulas.",
        },
        {
            "profile_code": "in_out_pressure_memo",
            "profile_ru_name": "Записка по нагрузке расходов на IN",
            "release_priority": "R2",
            "profile_status": "planned",
            "audience": "CFO / COO",
            "period_logic": "Monthly IN denominator context",
            "main_question": "Какие статьи растут непропорционально притоку денег?",
            "required_sections": pipe(["IN base", "Expense pressure", "MoM", "Plan-Fact", "Limitations"]),
            "source_signal_types": pipe(["flow_pressure", "plan_fact_scale", "mom_instability"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_flow_base_month", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_plan_fact_article_month", "slice_mom_article_month"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until IN pressure narrative template is approved.",
            "stop_conditions": "Missing IN denominator or IN-OUT summed across article rows.",
            "limitations": "Profile uses accepted proportionality metrics only.",
        },
        {
            "profile_code": "source_mix_reconciliation_memo",
            "profile_ru_name": "Записка по source_mix и сверкам",
            "release_priority": "R2",
            "profile_status": "planned",
            "audience": "Finance / Audit",
            "period_logic": "Current MART build scope",
            "main_question": "Насколько можно доверять источникам, reconciliation, plan_only/fact_only?",
            "required_sections": pipe(["Source mix", "Plan only", "Fact only", "Reconciliation", "DQ flags"]),
            "source_signal_types": pipe(["source_quality", "counterparty_quality"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_source_mix_summary", "slice_plan_only", "slice_fact_only", "slice_reconciliation_scope", "slice_dq_flags"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until audit memo template is approved.",
            "stop_conditions": "No reconciliation scope.",
            "limitations": "Does not replace audit sign-off.",
        },
        {
            "profile_code": "timing_candidates_memo",
            "profile_ru_name": "Записка по timing-кандидатам",
            "release_priority": "R3",
            "profile_status": "planned",
            "audience": "Finance / Budget owners",
            "period_logic": "Monthly candidate timing context",
            "main_question": "Что может быть переносом платежа?",
            "required_sections": pipe(["Timing candidates", "Expected reversal", "Confidence", "Owner validation"]),
            "source_signal_types": pipe(["timing_candidate"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_timing_candidates_by_article", "slice_timing_candidates_by_cfo", "slice_timing_month_shift_candidates"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until timing confirmation workflow exists.",
            "stop_conditions": "No timing basis or confidence.",
            "limitations": "Timing is candidate status, not confirmed conclusion.",
        },
        {
            "profile_code": "refund_impact_memo",
            "profile_ru_name": "Записка по влиянию player refunds",
            "release_priority": "R3",
            "profile_status": "planned",
            "audience": "Finance / Operations",
            "period_logic": "Monthly refund impact context",
            "main_question": "Как refunds влияют на факт, YoY, MoM и IN ratios?",
            "required_sections": pipe(["Refund impact", "Fact impact", "YoY/MoM context", "Limitations"]),
            "source_signal_types": pipe(["refund_impact", "yoy_shift", "mom_instability", "flow_pressure"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_player_refunds", "slice_refund_impact_by_month", "slice_refund_impact_by_article"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until refund treatment policy is approved.",
            "stop_conditions": "Refund rows missing or not separated from ordinary rows.",
            "limitations": "Does not change refund classification or formulas.",
        },
        {
            "profile_code": "currency_legal_entity_memo",
            "profile_ru_name": "Записка по валютам и юрлицам",
            "release_priority": "R2",
            "profile_status": "planned",
            "audience": "Finance / Treasury / Legal",
            "period_logic": "Current MART build scope",
            "main_question": "Где валютный и юридический контур расходов влияет на интерпретацию?",
            "required_sections": pipe(["Legal entities", "Currency exposure", "Non-EUR", "FX quality"]),
            "source_signal_types": pipe(["currency_exposure", "source_quality"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_legal_entity_fact", "slice_legal_entity_delta", "slice_currency_exposure", "slice_non_eur_operations"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until treasury/legal review template is approved.",
            "stop_conditions": "No legal entity or currency fields.",
            "limitations": "Does not create new FX rates or legal conclusions.",
        },
        {
            "profile_code": "counterparty_concentration_memo",
            "profile_ru_name": "Записка по концентрации контрагентов",
            "release_priority": "R3",
            "profile_status": "planned",
            "audience": "CFO / Procurement / Finance",
            "period_logic": "Current MART build scope",
            "main_question": "Насколько расходы сконцентрированы на топ-контрагентах?",
            "required_sections": pipe(["Top counterparties", "Concentration", "Quality limitations", "Actions"]),
            "source_signal_types": pipe(["counterparty_quality", "plan_fact_scale"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_full_budget"]),
            "source_slices": pipe(["slice_counterparty_concentration", "slice_counterparty_top_by_fact", "slice_counterparty_top_by_delta"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until procurement action policy is approved.",
            "stop_conditions": "Counterparty quality blocker without limitation label.",
            "limitations": "Concentration does not imply procurement conclusion without owner review.",
        },
        {
            "profile_code": "forecast_run_rate_memo",
            "profile_ru_name": "Записка по run-rate прогнозу",
            "release_priority": "R3",
            "profile_status": "planned",
            "audience": "CFO / COO",
            "period_logic": "Future forecast period; current MART has historical/monthly context only",
            "main_question": "Какой прогноз до конца месяца или квартала по текущему темпу?",
            "required_sections": pipe(["Run-rate base", "MoM context", "IN pressure", "Forecast limitations"]),
            "source_signal_types": pipe(["mom_instability", "flow_pressure"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_flow_base_month"]),
            "source_slices": pipe(["slice_mom_article_month", "slice_mom_signal_classification"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Blocked for final memo until forecast methodology is approved; preview can show source signals.",
            "stop_conditions": "No approved forecast formula or partial-period grain.",
            "limitations": "No forecast formulas are created in this task.",
        },
        {
            "profile_code": "budget_owner_action_register_memo",
            "profile_ru_name": "Реестр действий владельцев бюджета",
            "release_priority": "R3",
            "profile_status": "planned",
            "audience": "CFO / Finance PMO",
            "period_logic": "Current signal catalog scope",
            "main_question": "Что проверить, кто owner, срок и статус?",
            "required_sections": pipe(["Action register", "Owners", "Due dates", "Evidence", "Limitations"]),
            "source_signal_types": pipe(["planning_risk", "localization_concentration", "counterparty_quality", "source_quality"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_compact_executive_yoy_mom"]),
            "source_slices": pipe(["slice_localization_owner_route", "slice_planning_risk_candidates", "slice_dq_flags"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until owner/due-date workflow is approved.",
            "stop_conditions": "Action without owner or due date in final mode.",
            "limitations": "Current compact due_date is placeholder; no workflow state is changed.",
        },
        {
            "profile_code": "board_level_budget_summary",
            "profile_ru_name": "Board-level summary по бюджету",
            "release_priority": "R3",
            "profile_status": "planned",
            "audience": "CEO / Board-lite",
            "period_logic": "Executive selected period",
            "main_question": "Какие 5-7 верхнеуровневых выводов, рисков и действий стоит вынести наверх?",
            "required_sections": pipe(["Top insights", "Risks", "Actions", "Limitations", "Appendix pointer"]),
            "source_signal_types": pipe(["plan_fact_scale", "yoy_shift", "mom_instability", "planning_risk", "counterparty_quality", "flow_pressure"]),
            "source_marts": pipe(["mart_signal_catalog_full", "mart_main_compact_executive_yoy_mom"]),
            "source_slices": pipe(["slice_plan_fact_article", "slice_yoy_article", "slice_mom_article", "slice_planning_risk_candidates"]),
            "compact_mart_name": "mart_main_compact_executive_yoy_mom",
            "readiness_rules": "Preview only until board-level profile and wording rules are approved.",
            "stop_conditions": "Ungrounded executive conclusion or missing limitation text.",
            "limitations": "Does not generate board memo or final conclusions.",
        },
    ]
    return pd.DataFrame(profiles)


def add_profile_governance(profile_catalog: pd.DataFrame) -> pd.DataFrame:
    governance_defaults = {
        "block_status": "should",
        "output_layer": "finance_working_package",
        "publish_rule": "Publish as preview only until profile-specific DOCX contract is approved.",
        "acceptance_criteria": "Profile has source signals, risk_basis for risks, evidence_id/source_slice traceability, and documented limitations.",
        "evidence_requirement": "Each published signal must trace to mart_signal_catalog_full and source_slice/evidence_id.",
        "confidence_rule": "Low confidence must be labeled as limitation and must not be written as final fact.",
        "action_requirement": "Action is valid only when owner_candidate, due_date, and status are present; otherwise publish as recommendation candidate.",
    }
    by_profile: dict[str, dict[str, str]] = {
        "executive_yoy_mom_budget_memo": {
            "block_status": "must",
            "output_layer": "executive_memo",
            "publish_rule": "Publish only concise executive memo; evidence appendix supports but must not replace the memo.",
            "acceptance_criteria": "Executive profile requires plan/fact, YoY or MoM, flow context when used, risk_basis, confidence label, and evidence traceability.",
        },
        "monthly_plan_fact_memo": {
            "block_status": "must",
            "output_layer": "finance_working_package",
            "publish_rule": "Publish for Finance review after reconciliation and source QA pass.",
        },
        "weekly_coo_cash_cost_memo": {
            "block_status": "should",
            "output_layer": "operating_model",
            "publish_rule": "Do not publish final weekly memo until weekly/MTD grain is approved; monthly data supports preview only.",
        },
        "planning_risk_memo": {
            "block_status": "must",
            "output_layer": "finance_working_package",
            "publish_rule": "Publish planning risk as future budget risk, not as actual execution conclusion.",
        },
        "data_quality_blocker_memo": {
            "block_status": "must",
            "output_layer": "system_layer",
            "publish_rule": "DQ Fail blocks management conclusion until resolved or explicitly limited.",
            "acceptance_criteria": "Must identify blocker source, affected profile/output layer, and whether management conclusions are blocked.",
        },
        "article_deep_dive_memo": {"block_status": "should"},
        "cfo_owner_localization_memo": {
            "block_status": "should",
            "output_layer": "operating_model",
        },
        "counterparty_quality_memo": {
            "block_status": "should",
            "output_layer": "system_layer",
            "publish_rule": "Publish as data quality working package; strong counterparty conclusion is blocked when quality fails.",
        },
        "quarterly_budget_dynamics_review": {"block_status": "conditional"},
        "in_out_pressure_memo": {
            "block_status": "conditional",
            "publish_rule": "Publish IN/OUT/IN-OUT analysis only when Definition Card is present and IN denominator is valid.",
            "acceptance_criteria": "Requires Definition Card for IN, OUT, IN-OUT and proof that service rows are not mixed into expense deviations.",
            "evidence_requirement": "Must include mart_flow_base_month and the Definition Card reference.",
        },
        "source_mix_reconciliation_memo": {
            "block_status": "should",
            "output_layer": "system_layer",
        },
        "timing_candidates_memo": {"block_status": "conditional"},
        "refund_impact_memo": {"block_status": "conditional"},
        "currency_legal_entity_memo": {"block_status": "conditional"},
        "counterparty_concentration_memo": {"block_status": "conditional"},
        "forecast_run_rate_memo": {
            "block_status": "optional",
            "publish_rule": "Forecast/run-rate is optional and must not be default; publish only after forecast methodology approval.",
            "acceptance_criteria": "Requires approved forecast formula, partial-period grain, and confidence limitation.",
        },
        "budget_owner_action_register_memo": {
            "block_status": "conditional",
            "output_layer": "operating_model",
            "publish_rule": "Publish action register only when actions have owner, due date, and status.",
            "action_requirement": "Action rows require owner_candidate, due_date, and status; otherwise keep as candidate action.",
        },
        "board_level_budget_summary": {
            "block_status": "optional",
            "output_layer": "executive_memo",
            "publish_rule": "Board-level summary is optional and must use only grounded high-confidence executive signals.",
            "acceptance_criteria": "Requires 5-7 grounded signals with risk_basis, confidence label, evidence, and no DQ blockers.",
        },
    }

    enriched = profile_catalog.copy()
    for column, value in governance_defaults.items():
        enriched[column] = value

    for profile_code, overrides in by_profile.items():
        mask = enriched["profile_code"] == profile_code
        for column, value in overrides.items():
            enriched.loc[mask, column] = value

    conditional_in_out = enriched["source_signal_types"].fillna("").str.contains("flow_pressure", regex=False)
    enriched.loc[conditional_in_out, "confidence_rule"] = (
        "IN/OUT/IN-OUT use is conditional on Definition Card; low confidence remains limitation, not final fact."
    )
    enriched.loc[conditional_in_out, "evidence_requirement"] = enriched.loc[
        conditional_in_out, "evidence_requirement"
    ] + " Include Definition Card and mart_flow_base_month when flow metrics are used."
    enriched["stop_conditions"] = enriched["stop_conditions"] + (
        " DQ Fail blocks management conclusion. Risk without risk_basis is not publishable. "
        "Evidence appendix must not replace the executive memo."
    )
    enriched["readiness_rules"] = enriched["readiness_rules"] + (
        " Readiness is blocked/partial/ready according to publish_rule, DQ status, confidence, evidence, and action requirements."
    )
    default_depth_by_layer = {
        "executive_memo": "depth_2_management_memo",
        "finance_working_package": "depth_3_finance_working_package",
        "system_layer": "depth_3_finance_working_package",
        "operating_model": "depth_4_operating_model",
    }
    allowed_depth_by_layer = {
        "executive_memo": pipe(["depth_1_executive_brief", "depth_2_management_memo", "depth_3_finance_working_package", "depth_4_operating_model"]),
        "finance_working_package": pipe(["depth_3_finance_working_package", "depth_4_operating_model"]),
        "system_layer": pipe(["depth_3_finance_working_package"]),
        "operating_model": pipe(["depth_4_operating_model", "depth_3_finance_working_package"]),
    }
    enriched["default_depth_mode"] = enriched["output_layer"].map(default_depth_by_layer).fillna("depth_2_management_memo")
    enriched["allowed_depth_modes"] = enriched["output_layer"].map(allowed_depth_by_layer).fillna("depth_2_management_memo")
    enriched.loc[enriched["profile_code"].eq("executive_yoy_mom_budget_memo"), "allowed_depth_modes"] = pipe(
        ["depth_1_executive_brief", "depth_2_management_memo", "depth_3_finance_working_package", "depth_4_operating_model"]
    )
    enriched.loc[enriched["profile_code"].eq("monthly_plan_fact_memo"), "default_depth_mode"] = "depth_2_management_memo"
    enriched.loc[enriched["profile_code"].eq("monthly_plan_fact_memo"), "allowed_depth_modes"] = pipe(
        ["depth_2_management_memo", "depth_3_finance_working_package", "depth_4_operating_model"]
    )
    enriched.loc[enriched["profile_code"].eq("weekly_coo_cash_cost_memo"), "default_depth_mode"] = "depth_1_executive_brief"
    enriched.loc[enriched["profile_code"].eq("data_quality_blocker_memo"), "default_depth_mode"] = "depth_3_finance_working_package"
    enriched.loc[enriched["profile_code"].eq("budget_owner_action_register_memo"), "default_depth_mode"] = "depth_4_operating_model"
    return enriched


def explode_pipe(value: Any) -> list[str]:
    if pd.isna(value):
        return []
    return [part.strip() for part in str(value).split("|") if part.strip()]


def build_profile_lookup(profile_catalog: pd.DataFrame) -> dict[str, list[dict[str, Any]]]:
    lookup: dict[str, list[dict[str, Any]]] = {}
    for profile in profile_catalog.to_dict("records"):
        for signal_type in explode_pipe(profile["source_signal_types"]):
            lookup.setdefault(signal_type, []).append(profile)
    for profiles in lookup.values():
        profiles.sort(key=lambda item: (RELEASE_RANK.get(item["release_priority"], 99), item["profile_code"]))
    return lookup


def assign_signal_profiles(signals: pd.DataFrame, profile_catalog: pd.DataFrame) -> pd.DataFrame:
    profile_lookup = build_profile_lookup(profile_catalog)
    updated = signals.copy()
    eligible_values: list[str] = []
    primary_values: list[str] = []
    priority_values: list[int] = []
    release_values: list[str] = []
    status_values: list[str] = []

    for signal_type in updated["signal_type"].fillna("").astype(str):
        eligible_profiles = profile_lookup.get(signal_type, [])
        eligible_codes = [profile["profile_code"] for profile in eligible_profiles]
        primary = eligible_profiles[0] if eligible_profiles else None
        eligible_values.append(pipe(eligible_codes))
        primary_values.append(primary["profile_code"] if primary else "")
        priority_values.append(RELEASE_RANK.get(primary["release_priority"], 99) if primary else 99)
        release_values.append(primary["release_priority"] if primary else "")
        status_values.append("ready" if primary and primary["release_priority"] == "R1" else ("preview_only" if primary else "blocked"))

    updated["eligible_memo_profiles"] = eligible_values
    updated["primary_memo_profile"] = primary_values
    updated["profile_priority"] = priority_values
    updated["release_priority"] = release_values
    updated["profile_readiness_status"] = status_values
    if "memo_section" not in updated.columns:
        updated["memo_section"] = ""
    return updated


def assign_compact_profiles(compact: pd.DataFrame, updated_signals: pd.DataFrame) -> pd.DataFrame:
    join_fields = ["evidence_id", "eligible_memo_profiles", "primary_memo_profile", "profile_priority", "release_priority", "profile_readiness_status"]
    updated = compact.drop(columns=join_fields[1:], errors="ignore").copy()
    if "evidence_id" not in updated.columns:
        for field in join_fields[1:]:
            updated[field] = ""
        return updated

    signal_profile_fields = updated_signals[join_fields].drop_duplicates("evidence_id")
    updated = updated.merge(signal_profile_fields, on="evidence_id", how="left", suffixes=("", "_profile"))
    for field in join_fields[1:]:
        updated[field] = updated[field].fillna("")
    return updated


def build_readiness(profile_catalog: pd.DataFrame, updated_signals: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for profile in profile_catalog.to_dict("records"):
        code = profile["profile_code"]
        profile_signals = updated_signals[
            updated_signals["eligible_memo_profiles"].fillna("").astype(str).str.contains(code, regex=False)
        ].copy()
        signal_count = int(len(profile_signals))
        high_count = int((profile_signals["risk_level"].fillna("").astype(str).str.lower() == "high").sum()) if signal_count else 0
        qc_count = int(profile_signals["signal_type"].isin(QC_SIGNAL_TYPES).sum()) if signal_count else 0
        dq_fail_count = (
            int(profile_signals["qa_status"].fillna("").astype(str).str.lower().isin(["fail", "blocked"]).sum())
            if signal_count and "qa_status" in profile_signals.columns
            else 0
        )
        missing_risk_basis_count = (
            int(
                (
                    profile_signals["risk_level"].fillna("").astype(str).str.lower().isin(["high", "medium"])
                    & (profile_signals["risk_basis"].fillna("").astype(str).str.strip() == "")
                ).sum()
            )
            if signal_count and {"risk_level", "risk_basis"}.issubset(profile_signals.columns)
            else 0
        )

        if signal_count == 0:
            readiness_status = "blocked"
            data_readiness = "нет подходящих сигналов"
            limitation_reason = "Signal catalog has no entries matching profile source_signal_types."
            recommendation = "Do not build DOCX; inspect MART signal generation coverage."
            next_action = "Проверить покрытие source_signal_types."
        elif dq_fail_count > 0:
            readiness_status = "blocked"
            data_readiness = "DQ Fail blocks management conclusion"
            limitation_reason = "At least one eligible signal has QA fail/blocked status."
            recommendation = "Do not publish management conclusion until DQ blocker is resolved or explicitly limited."
            next_action = "Разобрать DQ blocker и обновить evidence/limitations."
        elif missing_risk_basis_count > 0:
            readiness_status = "blocked"
            data_readiness = "risk_basis missing"
            limitation_reason = "Risk signal without risk_basis is not publishable."
            recommendation = "Do not publish risk conclusion until risk_basis is populated."
            next_action = "Добавить risk_basis на уровне signal catalog после отдельного approval."
        elif profile["release_priority"] != "R1":
            readiness_status = "preview_only"
            data_readiness = "preview metadata available"
            limitation_reason = "Profile is planned for a later release; DOCX contract is not approved."
            recommendation = "Use preview index only; do not generate final memo."
            next_action = "Утвердить профиль, template и stop conditions перед DOCX."
        elif profile["block_status"] == "conditional":
            readiness_status = "partial"
            data_readiness = "conditional governance rule"
            limitation_reason = profile["publish_rule"]
            recommendation = "Use preview until conditional governance evidence is attached."
            next_action = "Подтвердить условие публикации и evidence requirement."
        elif code == "weekly_coo_cash_cost_memo":
            readiness_status = "partial"
            data_readiness = "monthly MART available; weekly grain missing"
            limitation_reason = "Accepted MART is monthly; weekly/MTD profile needs explicit weekly grain or period rule."
            recommendation = "Use as preview/partial until weekly source grain is approved."
            next_action = "Согласовать weekly/MTD period logic."
        else:
            readiness_status = "ready"
            data_readiness = "profile source signals available"
            limitation_reason = "No final DOCX generated in preview layer."
            recommendation = "Eligible for profile preview; DOCX generation requires separate approval."
            next_action = "Утвердить DOCX contract before report generation."

        allowed_depths = explode_pipe(profile.get("allowed_depth_modes", ""))
        ready_depths: list[str] = []
        partial_depths: list[str] = []
        blocked_depths: list[str] = []
        for depth in allowed_depths:
            if readiness_status == "blocked":
                blocked_depths.append(depth)
            elif depth == "depth_3_finance_working_package":
                ready_depths.append(depth)
            elif depth == "depth_4_operating_model":
                if profile["output_layer"] == "operating_model" or readiness_status == "ready":
                    partial_depths.append(depth)
                else:
                    blocked_depths.append(depth)
            elif readiness_status == "ready":
                ready_depths.append(depth)
            else:
                partial_depths.append(depth)
        depth_mode_readiness = pipe(
            [
                f"ready: {pipe(ready_depths) if ready_depths else '-'}",
                f"partial: {pipe(partial_depths) if partial_depths else '-'}",
                f"blocked: {pipe(blocked_depths) if blocked_depths else '-'}",
            ]
        )

        rows.append(
            {
                "profile_code": code,
                "profile_ru_name": profile["profile_ru_name"],
                "eligible_signal_count": signal_count,
                "high_risk_signal_count": high_count,
                "qc_blocker_signal_count": qc_count,
                "data_readiness": data_readiness,
                "readiness_status": readiness_status,
                "limitation_reason": limitation_reason,
                "recommendation": recommendation,
                "next_action": next_action,
                "default_depth_mode": profile.get("default_depth_mode", ""),
                "ready_depth_modes": pipe(ready_depths),
                "partial_depth_modes": pipe(partial_depths),
                "blocked_depth_modes": pipe(blocked_depths),
                "depth_mode_readiness": depth_mode_readiness,
            }
        )
    return pd.DataFrame(rows)


def build_preview(profile_catalog: pd.DataFrame, updated_signals: pd.DataFrame, readiness: pd.DataFrame) -> pd.DataFrame:
    readiness_by_code = readiness.set_index("profile_code").to_dict("index")
    rows: list[dict[str, Any]] = []
    for profile in profile_catalog.to_dict("records"):
        code = profile["profile_code"]
        profile_signals = updated_signals[
            updated_signals["eligible_memo_profiles"].fillna("").astype(str).str.contains(code, regex=False)
        ].copy()
        if "rank" in profile_signals.columns:
            profile_signals["rank_sort"] = pd.to_numeric(profile_signals["rank"], errors="coerce").fillna(999999)
        else:
            profile_signals["rank_sort"] = 999999
        profile_signals = profile_signals.sort_values(["rank_sort", "signal_id"], na_position="last")

        top_items: list[str] = []
        for signal in profile_signals.head(5).to_dict("records"):
            metric = signal.get("metric_value_eur", "")
            metric_text = "" if pd.isna(metric) else f"; EUR={metric}"
            top_items.append(f"{signal.get('signal_id', '')}: {signal.get('signal_type', '')} / {signal.get('object_name', '')}{metric_text}")

        available_signal_types = set(profile_signals["signal_type"].fillna("").astype(str))
        required_signal_types = set(explode_pipe(profile["source_signal_types"]))
        missing_types = sorted(required_signal_types - available_signal_types)
        required_sections = explode_pipe(profile["required_sections"])
        fillable_sections = required_sections if profile_signals.shape[0] else []
        readiness_row = readiness_by_code[code]
        can_build_docx = "да" if readiness_row["readiness_status"] == "ready" else "нет"

        rows.append(
            {
                "profile_code": code,
                "profile_ru_name": profile["profile_ru_name"],
                "top_5_signals": pipe(top_items) if top_items else "Нет подходящих сигналов",
                "fillable_sections": pipe(fillable_sections) if fillable_sections else "Нет разделов с подтвержденными сигналами",
                "missing_sections": pipe(missing_types) if missing_types else "Не выявлено по source_signal_types",
                "main_limitations": readiness_row["limitation_reason"],
                "can_build_docx": can_build_docx,
            }
        )
    return pd.DataFrame(rows)


def write_excel(path: Path, sheet_name: str, data: pd.DataFrame, mapping: dict[str, str]) -> None:
    visible = data[list(mapping.keys())].rename(columns=mapping)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        visible.to_excel(writer, index=False, sheet_name=sheet_name)
        worksheet = writer.sheets[sheet_name]
        worksheet.freeze_panes = "A2"
        for column_cells in worksheet.columns:
            header = str(column_cells[0].value)
            max_length = max(len(str(cell.value)) if cell.value is not None else 0 for cell in column_cells[:50])
            worksheet.column_dimensions[column_cells[0].column_letter].width = min(max(max_length + 2, len(header) + 2), 60)


def has_snake_case_header(headers: list[Any]) -> bool:
    for header in headers:
        text = str(header or "")
        if "_" in text and text.lower() == text:
            return True
    return False


def validate_excel_headers(path: Path, expected_sheet: str) -> bool:
    workbook = pd.ExcelFile(path)
    if expected_sheet not in workbook.sheet_names:
        return False
    headers = pd.read_excel(path, sheet_name=expected_sheet, nrows=0).columns.tolist()
    return not has_snake_case_header(headers)


def write_depth_template(depth_modes: pd.DataFrame) -> None:
    DEPTH_TEMPLATE_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Memo Depth Modes",
        "",
        "Depth mode is a controlled report-generation parameter. It changes presentation depth and artifact policy, not Stage, MART formulas, chart data, or memo logic.",
        "",
        "## Rules",
        "- Do not put all possible layers into every memo.",
        "- Separate executive memo from finance working package.",
        "- Forecast and scenarios are optional / advanced, not default.",
        "- IN / OUT / IN-OUT is conditional and requires Definition Card.",
        "- Risk must have risk_basis.",
        "- Low Confidence must not be written as final fact.",
        "- Action is valid only with owner / due date / status.",
        "- DQ Fail blocks management conclusion.",
        "- Evidence appendix must not replace executive memo.",
        "",
        "## Modes",
    ]
    for row in depth_modes.to_dict("records"):
        lines.extend(
            [
                "",
                f"### {row['depth_mode']} — {row['depth_mode_ru_name']}",
                f"- status: {row['depth_mode_status']}",
                f"- audience: {row['audience']}",
                f"- purpose: {row['purpose']}",
                f"- include: {row['included_sections']}",
                f"- exclude: {row['excluded_sections']}",
                f"- chart_policy: {row['chart_policy']}",
                f"- evidence_policy: {row['evidence_policy']}",
                f"- appendix_policy: {row['appendix_policy']}",
                f"- action_policy: {row['action_policy']}",
                f"- output_artifact_policy: {row['output_artifact_policy']}",
                f"- stop_conditions: {row['stop_conditions']}",
                f"- acceptance_criteria: {row['acceptance_criteria']}",
            ]
        )
    DEPTH_TEMPLATE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_depth_qa(depth_modes: pd.DataFrame, profile_catalog: pd.DataFrame, readiness: pd.DataFrame, raw_before: dict[str, tuple[int, int]], stage_before: dict[str, tuple[int, int]], build_marts_before: dict[str, tuple[int, int]]) -> dict[str, Any]:
    raw_after = snapshot_tree(RAW_DIR)
    stage_after = snapshot_tree(STAGE_DIR)
    build_marts_after = snapshot_file(BUILD_MARTS_SCRIPT)
    required_modes = {
        "depth_1_executive_brief",
        "depth_2_management_memo",
        "depth_3_finance_working_package",
        "depth_4_operating_model",
    }
    executive_modes = depth_modes[depth_modes["depth_mode"].isin(["depth_1_executive_brief", "depth_2_management_memo"])]
    finance = depth_modes[depth_modes["depth_mode"].eq("depth_3_finance_working_package")]
    operating = depth_modes[depth_modes["depth_mode"].eq("depth_4_operating_model")]
    checks = {
        "all_4_depth_modes_exist": set(depth_modes["depth_mode"]) == required_modes and len(depth_modes) == 4,
        "each_mode_has_included_excluded_sections": depth_modes["included_sections"].fillna("").ne("").all()
        and depth_modes["excluded_sections"].fillna("").ne("").all(),
        "each_mode_has_audience_and_artifact_policy": depth_modes["audience"].fillna("").ne("").all()
        and depth_modes["output_artifact_policy"].fillna("").ne("").all(),
        "executive_modes_do_not_include_full_evidence_dump": executive_modes["excluded_sections"].str.contains("full", case=False, regex=False).all()
        and executive_modes["evidence_policy"].str.contains("Compact", case=False, regex=False).all(),
        "finance_package_includes_evidence_and_slices": finance["included_sections"].str.contains("full evidence map", regex=False).all()
        and finance["included_sections"].str.contains("all memo slices", regex=False).all(),
        "operating_mode_includes_action_owner_due_status": operating["included_sections"].str.contains("owner", regex=False).all()
        and operating["included_sections"].str.contains("due date", regex=False).all()
        and operating["included_sections"].str.contains("status", regex=False).all(),
        "profile_catalog_has_default_allowed_depth_modes": {"default_depth_mode", "allowed_depth_modes"}.issubset(profile_catalog.columns)
        and profile_catalog["default_depth_mode"].fillna("").ne("").all()
        and profile_catalog["allowed_depth_modes"].fillna("").ne("").all(),
        "profile_readiness_has_depth_mode_readiness": {"default_depth_mode", "ready_depth_modes", "partial_depth_modes", "blocked_depth_modes", "depth_mode_readiness"}.issubset(readiness.columns),
        "depth_mode_excel_has_russian_visible_columns": validate_excel_headers(DEPTH_MODE_XLSX, "Режимы_Глубины"),
        "depth_template_exists": DEPTH_TEMPLATE_MD.exists(),
        "stage_untouched": stage_before == stage_after,
        "raw_untouched": raw_before == raw_after,
        "mart_formulas_untouched": build_marts_before == build_marts_after,
    }
    qa = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "pass" if all(bool(value) for value in checks.values()) else "fail",
        "checks": {key: bool(value) for key, value in checks.items()},
        "artifacts": [
            str(DEPTH_MODE_PARQUET.relative_to(PROJECT_ROOT)),
            str(DEPTH_MODE_XLSX.relative_to(PROJECT_ROOT)),
            str(DEPTH_TEMPLATE_MD.relative_to(PROJECT_ROOT)),
            str(DEPTH_QA_REPORT.relative_to(PROJECT_ROOT)),
            str(DEPTH_QA_SUMMARY.relative_to(PROJECT_ROOT)),
        ],
        "residual_risks": [
            "Depth mode is now a controlled contract parameter; individual generators still need explicit depth_mode implementation before generating alternate DOCX outputs.",
            "No new DOCX was generated in this task.",
        ],
    }
    DEPTH_QA_REPORT.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Depth Modes QA Summary",
        "",
        f"qa_status: {qa['qa_status']}",
        "",
        "## Checks",
        *[f"- {key}: {'pass' if value else 'fail'}" for key, value in qa["checks"].items()],
        "",
        "## Residual Risks",
        *[f"- {risk}" for risk in qa["residual_risks"]],
    ]
    DEPTH_QA_SUMMARY.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return qa


def main() -> None:
    timestamp = datetime.now(timezone.utc).isoformat()
    raw_before = snapshot_tree(RAW_DIR)
    stage_before = snapshot_tree(STAGE_DIR)
    build_marts_before = snapshot_file(BUILD_MARTS_SCRIPT)
    docx_before = snapshot_docx(REPORTS_DIR)

    required_inputs = [MART_MAIN_FULL, MART_FLOW, MART_SIGNAL_CATALOG, MART_COMPACT]
    missing_inputs = [str(path.relative_to(PROJECT_ROOT)) for path in required_inputs if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError(f"Missing accepted MART artifacts: {missing_inputs}")

    MARTS_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)

    signal_catalog = pd.read_parquet(MART_SIGNAL_CATALOG)
    compact = pd.read_parquet(MART_COMPACT)
    depth_modes = define_depth_modes()
    profile_catalog = add_profile_governance(define_profiles())
    updated_signals = assign_signal_profiles(signal_catalog, profile_catalog)
    updated_compact = assign_compact_profiles(compact, updated_signals)
    readiness = build_readiness(profile_catalog, updated_signals)
    preview = build_preview(profile_catalog, updated_signals, readiness)

    depth_modes.to_parquet(DEPTH_MODE_PARQUET, index=False)
    profile_catalog.to_parquet(PROFILE_CATALOG_PARQUET, index=False)
    readiness.to_parquet(READINESS_PARQUET, index=False)
    preview.to_parquet(PREVIEW_PARQUET, index=False)
    updated_signals.to_parquet(MART_SIGNAL_CATALOG, index=False)
    updated_compact.to_parquet(MART_COMPACT, index=False)

    write_excel(DEPTH_MODE_XLSX, "Режимы_Глубины", depth_modes, DEPTH_MODE_EXCEL_COLUMNS)
    write_excel(PROFILE_CATALOG_XLSX, "Профили_Записок", profile_catalog, CATALOG_EXCEL_COLUMNS)
    write_excel(READINESS_XLSX, "Матрица_Готовности", readiness, READINESS_EXCEL_COLUMNS)
    write_excel(PREVIEW_XLSX, "Preview_Профилей", preview, PREVIEW_EXCEL_COLUMNS)
    write_depth_template(depth_modes)

    raw_after = snapshot_tree(RAW_DIR)
    stage_after = snapshot_tree(STAGE_DIR)
    build_marts_after = snapshot_file(BUILD_MARTS_SCRIPT)
    docx_after = snapshot_docx(REPORTS_DIR)

    expected_codes = set(profile_catalog["profile_code"])
    r1_profiles = profile_catalog[profile_catalog["release_priority"] == "R1"]
    non_r1_profiles = profile_catalog[profile_catalog["release_priority"] != "R1"]
    qa_checks = {
        "all_18_profiles_exist": len(profile_catalog) == 18 and len(expected_codes) == 18,
        "r1_profiles_active": bool((r1_profiles["profile_status"] == "active").all()),
        "non_r1_profiles_planned": bool(non_r1_profiles["profile_status"].isin(["planned", "preview_only"]).all()),
        "signal_catalog_has_profile_eligibility_fields": all(field in updated_signals.columns for field in PROFILE_SIGNAL_FIELDS),
        "profile_catalog_has_governance_fields": all(
            field in profile_catalog.columns
            for field in [
                "block_status",
                "output_layer",
                "publish_rule",
                "acceptance_criteria",
                "evidence_requirement",
                "confidence_rule",
                "action_requirement",
            ]
        ),
        "profile_catalog_has_depth_mode_fields": {"default_depth_mode", "allowed_depth_modes"}.issubset(profile_catalog.columns),
        "profile_readiness_has_depth_mode_fields": {
            "default_depth_mode",
            "ready_depth_modes",
            "partial_depth_modes",
            "blocked_depth_modes",
            "depth_mode_readiness",
        }.issubset(readiness.columns),
        "all_4_depth_modes_exist": len(depth_modes) == 4
        and set(depth_modes["depth_mode"])
        == {
            "depth_1_executive_brief",
            "depth_2_management_memo",
            "depth_3_finance_working_package",
            "depth_4_operating_model",
        },
        "forecast_and_scenario_not_default": bool(
            profile_catalog.loc[
                profile_catalog["profile_code"] == "forecast_run_rate_memo", "block_status"
            ].eq("optional").all()
        ),
        "in_out_requires_definition_card": bool(
            profile_catalog.loc[
                profile_catalog["source_signal_types"].fillna("").str.contains("flow_pressure", regex=False),
                "evidence_requirement",
            ].str.contains("Definition Card", regex=False).all()
        ),
        "profile_readiness_matrix_exists": READINESS_PARQUET.exists() and READINESS_XLSX.exists(),
        "profile_preview_index_exists": PREVIEW_PARQUET.exists() and PREVIEW_XLSX.exists(),
        "excel_files_have_russian_visible_columns": all(
            [
                validate_excel_headers(PROFILE_CATALOG_XLSX, "Профили_Записок"),
                validate_excel_headers(READINESS_XLSX, "Матрица_Готовности"),
                validate_excel_headers(PREVIEW_XLSX, "Preview_Профилей"),
                validate_excel_headers(DEPTH_MODE_XLSX, "Режимы_Глубины"),
            ]
        ),
        "no_docx_reports_generated_or_modified": docx_before == docx_after,
        "stage_untouched": stage_before == stage_after,
        "raw_untouched": raw_before == raw_after,
        "mart_formulas_untouched": build_marts_before == build_marts_after,
        "profile_preview_mode": True,
    }
    qa_status = "pass" if all(qa_checks.values()) else "fail"
    qa_report = {
        "timestamp": timestamp,
        "qa_status": qa_status,
        "inputs": [str(path.relative_to(PROJECT_ROOT)) for path in required_inputs],
        "generated_profile_artifacts": [
            str(DEPTH_MODE_PARQUET.relative_to(PROJECT_ROOT)),
            str(PROFILE_CATALOG_PARQUET.relative_to(PROJECT_ROOT)),
            str(READINESS_PARQUET.relative_to(PROJECT_ROOT)),
            str(PREVIEW_PARQUET.relative_to(PROJECT_ROOT)),
        ],
        "excel_artifacts": [
            str(DEPTH_MODE_XLSX.relative_to(PROJECT_ROOT)),
            str(PROFILE_CATALOG_XLSX.relative_to(PROJECT_ROOT)),
            str(READINESS_XLSX.relative_to(PROJECT_ROOT)),
            str(PREVIEW_XLSX.relative_to(PROJECT_ROOT)),
        ],
        "updated_mart_artifacts": [
            str(MART_SIGNAL_CATALOG.relative_to(PROJECT_ROOT)),
            str(MART_COMPACT.relative_to(PROJECT_ROOT)),
        ],
        "qa_artifacts": [
            str(QA_REPORT.relative_to(PROJECT_ROOT)),
            str(QA_SUMMARY.relative_to(PROJECT_ROOT)),
            str(DEPTH_QA_REPORT.relative_to(PROJECT_ROOT)),
            str(DEPTH_QA_SUMMARY.relative_to(PROJECT_ROOT)),
        ],
        "checks": qa_checks,
        "profile_count": int(len(profile_catalog)),
        "r1_profile_count": int(len(r1_profiles)),
        "readiness_status_counts": readiness["readiness_status"].value_counts().to_dict(),
        "docx_generated": "no" if qa_checks["no_docx_reports_generated_or_modified"] else "yes",
        "residual_risks": [
            "Profile readiness is metadata/preview only; DOCX profile contracts and narrative templates still require approval.",
            "Weekly COO and forecast profiles need explicit weekly/MTD or forecast methodology before final report generation.",
            "Updating signal/compact artifacts adds profile eligibility fields but does not change formulas or source metrics.",
            "Depth mode is a controlled contract parameter; alternate-depth DOCX/report generators still need explicit implementation.",
        ],
    }
    QA_REPORT.write_text(json.dumps(qa_report, ensure_ascii=False, indent=2), encoding="utf-8")

    summary_lines = [
        "# Memo Profile Catalog QA Summary",
        "",
        f"- Timestamp: {timestamp}",
        f"- QA status: {qa_status}",
        f"- Profiles: {len(profile_catalog)}",
        f"- R1 active profiles: {len(r1_profiles)}",
        f"- Readiness status counts: {qa_report['readiness_status_counts']}",
        f"- Stage untouched: {qa_checks['stage_untouched']}",
        f"- Raw untouched: {qa_checks['raw_untouched']}",
        f"- MART formulas untouched: {qa_checks['mart_formulas_untouched']}",
        f"- DOCX generated or modified: {qa_report['docx_generated']}",
        "",
        "## Checks",
    ]
    summary_lines.extend([f"- {name}: {value}" for name, value in qa_checks.items()])
    QA_SUMMARY.write_text("\n".join(summary_lines) + "\n", encoding="utf-8")
    depth_qa = write_depth_qa(depth_modes, profile_catalog, readiness, raw_before, stage_before, build_marts_before)

    print(
        json.dumps(
            {
                "qa_status": qa_status,
                "depth_modes_qa_status": depth_qa["qa_status"],
                "profile_count": len(profile_catalog),
                "depth_mode_count": len(depth_modes),
                "checks": qa_checks,
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
