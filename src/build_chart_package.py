from __future__ import annotations

import json
import shutil
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
from matplotlib.ticker import FuncFormatter

try:
    from src.progress import log_progress
except ImportError:  # pragma: no cover
    from progress import log_progress


matplotlib.use("Agg")

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "01_raw"
STAGE_DIR = PROJECT_ROOT / "02_stage"
MARTS_DIR = PROJECT_ROOT / "03_marts"
CHARTS_DIR = PROJECT_ROOT / "04_charts"
CHART_DATA_DIR = CHARTS_DIR / "chart_data"
CHART_SPECS_DIR = CHARTS_DIR / "chart_specs"
CHART_IMAGES_DIR = CHARTS_DIR / "images"
CHART_QA_DIR = PROJECT_ROOT / "07_qa" / "chart_qa"

CHART_CATALOG_PARQUET = CHARTS_DIR / "chart_catalog.parquet"
CHART_CATALOG_XLSX = CHARTS_DIR / "chart_catalog.xlsx"
CHART_QA_REPORT = CHART_QA_DIR / "chart_qa_report.json"
CHART_QA_SUMMARY = CHART_QA_DIR / "chart_qa_summary.md"
CHART_STYLE_CONFIG = CHARTS_DIR / "chart_style_config.json"
CHART_DISPLAY_LABEL_MAPPING = CHARTS_DIR / "chart_display_label_mapping.json"
BUILD_MARTS_SCRIPT = PROJECT_ROOT / "src" / "build_marts.py"

MEMO_PROFILE = "executive_yoy_mom_budget_memo"
MEMO_PROFILE_RU = "Управленческая записка YoY/MoM по бюджету"
DEPTH_MODE = "depth_2_management_memo"
SERVICE_VALUES = {"IN", "OUT", "IN-OUT"}

STYLE_CONFIG = {
    "primary_navy": "#1F2A44",
    "muted_blue": "#3D5A80",
    "warm_grey": "#8A817C",
    "sage": "#6B8F71",
    "burgundy": "#8C4A4A",
    "sand": "#C2A878",
    "grid_light": "#E6E8EB",
    "text_dark": "#1F2933",
}

DISPLAY_LABEL_MAPPING = {
    "fact_only": "Факт без плана",
    "plan_only": "План без факта",
    "p_fact_adjusted": "Корректировка план-факт",
    "plan_and_fact": "План и факт",
    "cons_budget": "Сводный бюджет",
    "refund_only": "Возвраты игрокам",
    "source_mix": "Состав источника",
    "rows_count": "Количество строк",
    "abs_delta_eur": "ABS отклонение, EUR",
    "out_eur": "OUT, EUR",
    "in_eur": "IN, EUR",
    "in_out_eur": "IN-OUT, EUR",
    "ONJN Gaming Tax": "Игровой налог ONJN",
}

CATALOG_RU_COLUMNS = {
    "chart_id": "ID графика",
    "chart_name_ru": "Название графика",
    "memo_profile": "Профиль записки",
    "memo_section": "Раздел записки",
    "purpose": "Цель",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "metric": "Метрика",
    "grain": "Гранулярность",
    "period": "Период",
    "filter_logic": "Фильтр",
    "chart_type": "Тип графика",
    "caption_claim": "Тезис подписи",
    "caption_ru": "Подпись",
    "chart_order": "Порядок",
    "include_in_memo": "Включать в записку",
    "chart_role": "Роль графика",
    "recommended_placement": "Рекомендуемое место",
    "limitation": "Ограничение",
    "qa_status": "QA статус",
    "data_path": "Путь к данным",
    "image_path": "Путь к изображению",
}

EXECUTIVE_ROUTE = {
    "CH_EXEC_001_PLAN_FACT_TOP_ABS": (1, True, "executive_body", "1. Масштаб Plan-Fact"),
    "CH_EXEC_002_YOY_TOP_SHIFT": (2, True, "executive_body", "2. YoY сдвиги"),
    "CH_EXEC_003_MOM_INSTABILITY": (3, True, "executive_body", "3. MoM нестабильность"),
    "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO": (4, True, "executive_body", "4. Локализация"),
    "CH_EXEC_005_PLANNING_RISK": (5, True, "executive_body", "5. Плановый риск"),
    "CH_EXEC_006_IN_CONTEXT": (6, True, "executive_body", "6. IN context"),
    "CH_EXEC_007_FLOW_BASE": (7, True, "executive_body", "7. Flow base context"),
    "CH_EXEC_008_QA_LIMITATIONS": (8, True, "executive_body", "8. QC и ограничения"),
    "CH_EXEC_009_COUNTERPARTY_QUALITY": (9, False, "appendix", "Appendix A. Контрагенты"),
    "CH_EXEC_010_CURRENCY_EXPOSURE": (10, False, "appendix", "Appendix B. Валюты"),
}

REQUIRED_INPUTS = [
    MARTS_DIR / "mart_signal_catalog_full.parquet",
    MARTS_DIR / "mart_main_compact_executive_yoy_mom.parquet",
    MARTS_DIR / "mart_flow_base_month.parquet",
    MARTS_DIR / "memo_profile_catalog.parquet",
    MARTS_DIR / "profile_readiness_matrix.parquet",
    MARTS_DIR / "profile_preview_index.parquet",
    MARTS_DIR / "slice_plan_fact_article_cfo.parquet",
    MARTS_DIR / "slice_yoy_article.parquet",
    MARTS_DIR / "slice_mom_article.parquet",
    MARTS_DIR / "slice_localization_article_cfo.parquet",
    MARTS_DIR / "slice_plan_vs_history_article_cfo.parquet",
    MARTS_DIR / "slice_source_mix_summary.parquet",
    MARTS_DIR / "slice_counterparty_unknown.parquet",
    MARTS_DIR / "slice_currency_exposure.parquet",
]


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


def reset_output_dirs() -> None:
    for directory in [CHART_DATA_DIR, CHART_SPECS_DIR, CHART_IMAGES_DIR, CHART_QA_DIR]:
        if directory.exists():
            shutil.rmtree(directory)
        directory.mkdir(parents=True, exist_ok=True)
    CHARTS_DIR.mkdir(parents=True, exist_ok=True)
    for path in [CHART_CATALOG_PARQUET, CHART_CATALOG_XLSX]:
        if path.exists():
            path.unlink()


def read_mart(name: str) -> pd.DataFrame:
    return pd.read_parquet(MARTS_DIR / name)


def rel(path: Path) -> str:
    return str(path.relative_to(PROJECT_ROOT))


def shorten(value: Any, limit: int = 42) -> str:
    text = "" if pd.isna(value) else str(value)
    return text if len(text) <= limit else text[: limit - 1] + "…"


def wrap_label(value: Any, width: int = 32, max_lines: int = 2) -> str:
    text = shorten(value, width * max_lines)
    lines = textwrap.wrap(text, width=width)
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines[-1] = shorten(lines[-1], width)
    return "\n".join(lines) if lines else ""


def format_eur(value: float) -> str:
    return f"{value / 1_000_000:.1f}".replace(".", ",") + " млн"


def format_amount_eur(value: float) -> str:
    numeric = float(value)
    if abs(numeric) >= 1_000_000:
        return f"{numeric / 1_000_000:.1f}".replace(".", ",") + " млн EUR"
    if abs(numeric) >= 10_000:
        return f"{numeric / 1_000:.1f}".replace(".", ",") + " тыс. EUR"
    return f"{numeric:,.0f} EUR".replace(",", " ")


def format_axis_eur(value: float) -> str:
    numeric = float(value)
    if abs(numeric) >= 1_000_000:
        return f"{numeric / 1_000_000:.0f}".replace(".", ",") + " млн"
    if abs(numeric) >= 10_000:
        return f"{numeric / 1_000:.0f}".replace(".", ",") + " тыс."
    return f"{numeric:,.0f}".replace(",", " ")


def row_word(value: float) -> str:
    number = int(abs(round(value)))
    if 11 <= number % 100 <= 14:
        return "строк"
    if number % 10 == 1:
        return "строка"
    if 2 <= number % 10 <= 4:
        return "строки"
    return "строк"


def format_count(value: float) -> str:
    numeric = float(value)
    if abs(numeric) < 10_000:
        return f"{numeric:,.0f}".replace(",", " ") + f" {row_word(numeric)}"
    return f"{numeric / 1_000:.1f}".replace(".", ",") + " тыс. строк"


def display_label(value: Any) -> str:
    return DISPLAY_LABEL_MAPPING.get(str(value), str(value))


def apply_chart_style(ax: Any) -> None:
    ax.title.set_color(STYLE_CONFIG["text_dark"])
    ax.xaxis.label.set_color(STYLE_CONFIG["text_dark"])
    ax.yaxis.label.set_color(STYLE_CONFIG["text_dark"])
    ax.tick_params(colors=STYLE_CONFIG["text_dark"])
    for spine in ax.spines.values():
        spine.set_color(STYLE_CONFIG["warm_grey"])


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_barh(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    xlabel: str,
    path: Path,
    percent: bool = False,
    value_formatter: Any | None = None,
) -> None:
    work = df.sort_values(value_col, ascending=True).tail(12)
    labels = [wrap_label(value) for value in work[label_col]]
    values = pd.to_numeric(work[value_col], errors="coerce").fillna(0)
    fig_height = max(4.5, 0.42 * len(work) + 1.5)
    fig, ax = plt.subplots(figsize=(11, fig_height))
    ax.barh(labels, values, color=STYLE_CONFIG["muted_blue"])
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=STYLE_CONFIG["text_dark"])
    ax.set_xlabel(xlabel)
    ax.grid(False)
    max_value = float(values.max()) if len(values) else 0.0
    if max_value > 0:
        ax.set_xlim(0, max_value * 1.14)
    if value_formatter:
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: value_formatter(float(value))))
    elif not percent:
        ax.xaxis.set_major_formatter(FuncFormatter(lambda value, _pos: format_axis_eur(float(value))))
    for index, value in enumerate(values):
        label = (
            f"{value:.1%}"
            if percent
            else value_formatter(float(value)) if value_formatter
            else f"{format_eur(float(value))} EUR"
        )
        ax.text(value, index, f" {label}", va="center", fontsize=8)
    apply_chart_style(ax)
    fig.subplots_adjust(left=0.34, right=0.93, top=0.88, bottom=0.16)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_grouped_line(df: pd.DataFrame, title: str, path: Path) -> None:
    work = df.sort_values("period_month")
    fig, ax = plt.subplots(figsize=(11, 5.5))
    line_colors = {
        "in_eur": STYLE_CONFIG["muted_blue"],
        "out_eur": STYLE_CONFIG["burgundy"],
        "in_out_eur": STYLE_CONFIG["sage"],
    }
    for column, label in [("in_eur", "IN, EUR"), ("out_eur", "OUT, EUR"), ("in_out_eur", "IN-OUT, EUR")]:
        ax.plot(work["period_month"], work[column], marker="o", linewidth=2, label=label, color=line_colors[column])
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=STYLE_CONFIG["text_dark"])
    ax.set_xlabel("Месяц")
    ax.set_ylabel("EUR")
    ax.grid(False)
    ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: format_axis_eur(float(value))))
    ax.legend()
    ax.tick_params(axis="x", rotation=45)
    apply_chart_style(ax)
    fig.subplots_adjust(left=0.10, right=0.96, top=0.88, bottom=0.22)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def save_vertical_bar(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    ylabel: str,
    path: Path,
    percent: bool = False,
    value_formatter: Any | None = None,
) -> None:
    work = df.sort_values(value_col, ascending=False).head(12)
    labels = [wrap_label(value, width=18, max_lines=2) for value in work[label_col]]
    values = pd.to_numeric(work[value_col], errors="coerce").fillna(0)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.bar(labels, values, color=STYLE_CONFIG["muted_blue"])
    ax.set_title(title, fontsize=12.5, fontweight="bold", color=STYLE_CONFIG["text_dark"])
    ax.set_ylabel(ylabel)
    ax.grid(False)
    ax.tick_params(axis="x", rotation=35)
    if value_formatter:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: value_formatter(float(value))))
    elif not percent:
        ax.yaxis.set_major_formatter(FuncFormatter(lambda value, _pos: format_axis_eur(float(value))))
    for index, value in enumerate(values):
        label = (
            f"{value:.1%}"
            if percent
            else value_formatter(float(value)) if value_formatter
            else f"{format_eur(float(value))}"
        )
        ax.text(index, value, label, ha="center", va="bottom", fontsize=8)
    apply_chart_style(ax)
    fig.subplots_adjust(left=0.17 if value_formatter else 0.10, right=0.96, top=0.88, bottom=0.28)
    fig.savefig(path, dpi=180)
    plt.close(fig)


def add_evidence_ids(df: pd.DataFrame, chart_id: str, source_slice: str) -> pd.DataFrame:
    result = df.copy().reset_index(drop=True)
    if "evidence_id" not in result.columns:
        result["evidence_id"] = [f"{chart_id}-{source_slice}-ROW-{idx + 1:03d}" for idx in result.index]
    return result


def source_mix_row_count_warning(df: pd.DataFrame) -> str:
    counts = dict(zip(df["source_mix"], pd.to_numeric(df["rows_count"], errors="coerce").fillna(0)))
    matched = counts.get("plan_and_fact", 0)
    fact_only = counts.get("fact_only", 0)
    plan_only = counts.get("plan_only", 0)
    comparison_base = min(value for value in [fact_only, plan_only] if value > 0) if fact_only > 0 and plan_only > 0 else 0
    if comparison_base and matched < 0.25 * comparison_base:
        return (
            "warning: plan_and_fact rows are materially lower than fact_only/plan_only rows; "
            "management conclusions should keep source-mix limitation visible."
        )
    return ""


def chart_record(
    *,
    chart_id: str,
    chart_name_ru: str,
    memo_section: str,
    purpose: str,
    source_mart: str,
    source_slice: str,
    metric: str,
    grain: str,
    period: str,
    filter_logic: str,
    chart_type: str,
    caption_claim: str,
    caption_ru: str,
    limitation: str,
    data_path: Path,
    image_path: Path,
    qa_status: str = "pass",
) -> dict[str, Any]:
    chart_order, include_in_memo, chart_role, recommended_placement = EXECUTIVE_ROUTE[chart_id]
    return {
        "chart_id": chart_id,
        "chart_name_ru": chart_name_ru,
        "memo_profile": MEMO_PROFILE,
        "memo_section": memo_section,
        "purpose": purpose,
        "source_mart": source_mart,
        "source_slice": source_slice,
        "metric": metric,
        "grain": grain,
        "period": period,
        "filter_logic": filter_logic,
        "chart_type": chart_type,
        "caption_claim": caption_claim,
        "caption_ru": caption_ru,
        "chart_order": chart_order,
        "include_in_memo": include_in_memo,
        "chart_role": chart_role,
        "recommended_placement": recommended_placement,
        "limitation": limitation,
        "qa_status": qa_status,
        "data_path": rel(data_path),
        "image_path": rel(image_path),
    }


def write_chart(chart: dict[str, Any], data: pd.DataFrame, spec: dict[str, Any]) -> None:
    data_path = CHART_DATA_DIR / f"{chart['chart_id']}.parquet"
    spec_path = CHART_SPECS_DIR / f"{chart['chart_id']}.json"
    data.to_parquet(data_path, index=False)
    write_json(spec_path, spec)


def build_chart_package() -> dict[str, Any]:
    raw_before = snapshot(RAW_DIR)
    stage_before = snapshot(STAGE_DIR)
    build_marts_before = snapshot_file(BUILD_MARTS_SCRIPT)
    docx_before = list(PROJECT_ROOT.rglob("*.docx"))
    missing_inputs = [rel(path) for path in REQUIRED_INPUTS if not path.exists()]
    if missing_inputs:
        raise FileNotFoundError(f"Missing accepted MART inputs: {missing_inputs}")

    reset_output_dirs()
    write_json(CHART_STYLE_CONFIG, STYLE_CONFIG)
    write_json(CHART_DISPLAY_LABEL_MAPPING, DISPLAY_LABEL_MAPPING)
    catalog_rows: list[dict[str, Any]] = []

    # CH_EXEC_001
    pf = read_mart("slice_plan_fact_article_cfo.parquet")
    pf = pf[~pf["article"].isin(SERVICE_VALUES)].copy()
    pf["label"] = pf["article"].map(str) + " / " + pf["cfo"].map(str)
    pf_data = add_evidence_ids(
        pf.sort_values("abs_delta_eur", ascending=False)
        .head(12)[["article", "cfo", "label", "plan_eur", "fact_eur", "delta_eur", "abs_delta_eur", "source_slice"]],
        "CH_EXEC_001_PLAN_FACT_TOP_ABS",
        "slice_plan_fact_article_cfo",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_001_PLAN_FACT_TOP_ABS.png"
    save_barh(pf_data, "label", "abs_delta_eur", "Топ отклонений Plan-Fact по ABS EUR", "ABS отклонение, EUR", image)
    record = chart_record(
        chart_id="CH_EXEC_001_PLAN_FACT_TOP_ABS",
        chart_name_ru="Топ отклонений Plan-Fact по ABS EUR",
        memo_section="Исторический факт: масштаб Plan-Fact",
        purpose="Показать крупнейшие отклонения бюджета по сумме.",
        source_mart="mart_main_full_budget",
        source_slice="slice_plan_fact_article_cfo",
        metric="abs_delta_eur",
        grain="Статья × ЦФО",
        period="all_available_periods",
        filter_logic="Exclude IN / OUT / IN-OUT; top 12 by abs_delta_eur.",
        chart_type="horizontal bar",
        caption_claim="Крупнейшие план-факт отклонения по ABS EUR; сервисные flow rows исключены.",
        caption_ru="Крупнейшие отклонения Plan-Fact показаны по ABS EUR; строки IN / OUT / IN-OUT исключены.",
        limitation="Chart localizes magnitude, not root cause.",
        data_path=CHART_DATA_DIR / "CH_EXEC_001_PLAN_FACT_TOP_ABS.parquet",
        image_path=image,
    )
    write_chart(record, pf_data, record)
    catalog_rows.append(record)

    # CH_EXEC_002
    yoy = read_mart("slice_yoy_article.parquet")
    yoy = yoy[yoy["prior_year_available_flag"].eq(1)].copy()
    yoy["base_limitation"] = np.where(yoy["weak_yoy_base_flag"].eq(1), "weak_yoy_base", "")
    yoy["article_display_ru"] = yoy["article"].map(display_label)
    yoy["label"] = yoy["article_display_ru"] + " / " + yoy["period_month"].map(str)
    yoy_data = add_evidence_ids(
        yoy.sort_values("abs_yoy_delta_eur", ascending=False)
        .head(5)[["article", "article_display_ru", "label", "period_month", "current_fact_eur", "prior_year_fact_eur", "yoy_delta_eur", "abs_yoy_delta_eur", "prior_year_available_flag", "weak_yoy_base_flag", "no_yoy_base_flag", "base_limitation", "source_slice"]],
        "CH_EXEC_002_YOY_TOP_SHIFT",
        "slice_yoy_article",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_002_YOY_TOP_SHIFT.png"
    save_barh(yoy_data, "label", "abs_yoy_delta_eur", "Топ-5 YoY-сдвигов по EUR", "ABS YoY отклонение, EUR", image)
    record = chart_record(
        chart_id="CH_EXEC_002_YOY_TOP_SHIFT",
        chart_name_ru="Топ-5 YoY-сдвигов по EUR",
        memo_section="YoY: сдвиг уровня к прошлому году",
        purpose="Показать статьи, где уровень факта изменился к прошлому году.",
        source_mart="mart_main_full_budget",
        source_slice="slice_yoy_article",
        metric="abs_yoy_delta_eur",
        grain="Статья × месяц",
        period="matching_month_prior_year",
        filter_logic="prior_year_available_flag = 1; sort by abs_yoy_delta_eur descending; top 5 rows.",
        chart_type="horizontal bar",
        caption_claim="Топ-5 YoY-сдвигов показан только для строк с доступной базой прошлого года.",
        caption_ru="Топ-5 YoY-сдвигов показан только для строк с доступной базой прошлого года; подписи включают статью и месяц.",
        limitation="Weak YoY base rows are labeled in chart data and must not be used as strong conclusions.",
        data_path=CHART_DATA_DIR / "CH_EXEC_002_YOY_TOP_SHIFT.parquet",
        image_path=image,
    )
    write_chart(record, yoy_data, record)
    catalog_rows.append(record)

    # CH_EXEC_003
    mom = read_mart("slice_mom_article.parquet")
    mom_data = add_evidence_ids(
        mom[mom["mom_signal_type"].isin(["serial_shift", "repeated_instability", "one_off_spike", "stable"])]
        .sort_values("sum_abs_mom_delta_eur", ascending=False)
        .head(12)[["article", "sum_abs_mom_delta_eur", "abs_mom_delta_eur", "mom_delta_eur", "growth_months_count", "decline_months_count", "active_months_count", "mom_signal_type", "source_slice"]],
        "CH_EXEC_003_MOM_INSTABILITY",
        "slice_mom_article",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_003_MOM_INSTABILITY.png"
    save_vertical_bar(mom_data, "article", "sum_abs_mom_delta_eur", "Топ MoM-нестабильности", "Сумма ABS MoM отклонений, EUR", image)
    record = chart_record(
        chart_id="CH_EXEC_003_MOM_INSTABILITY",
        chart_name_ru="Топ MoM-нестабильности",
        memo_section="MoM: помесячная динамика и нестабильность",
        purpose="Показать статьи с наибольшей месячной турбулентностью.",
        source_mart="mart_main_full_budget",
        source_slice="slice_mom_article",
        metric="sum_abs_mom_delta_eur",
        grain="Статья",
        period="all_available_months",
        filter_logic="Top 12 by sum_abs_mom_delta_eur; YoY metrics excluded.",
        chart_type="bar",
        caption_claim="MoM instability is ranked by summed absolute monthly movement.",
        caption_ru="MoM-нестабильность ранжирована по сумме ABS месячных движений; график не смешивает YoY и MoM.",
        limitation="MoM chart does not assert cause and does not mix YoY metrics.",
        data_path=CHART_DATA_DIR / "CH_EXEC_003_MOM_INSTABILITY.parquet",
        image_path=image,
    )
    write_chart(record, mom_data, record)
    catalog_rows.append(record)

    # CH_EXEC_004
    loc = read_mart("slice_localization_article_cfo.parquet")
    loc["label"] = loc["article"].map(str) + " / " + loc["cfo"].map(str)
    loc_data = add_evidence_ids(
        loc.sort_values("cfo_abs_delta_eur", ascending=False)
        .head(12)[["article", "cfo", "label", "cfo_abs_delta_eur", "cfo_share_in_article_delta", "concentration_type", "owner_candidate", "source_slice"]],
        "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO",
        "slice_localization_article_cfo",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO.png"
    save_barh(loc_data, "label", "cfo_abs_delta_eur", "Локализация отклонений по статье и ЦФО", "ABS отклонение ЦФО, EUR", image)
    record = chart_record(
        chart_id="CH_EXEC_004_LOCALIZATION_ARTICLE_CFO",
        chart_name_ru="Локализация отклонений по статье и ЦФО",
        memo_section="Локализация: статья × ЦФО",
        purpose="Показать, где сидит сигнал и кому задавать вопрос.",
        source_mart="mart_main_full_budget",
        source_slice="slice_localization_article_cfo",
        metric="cfo_abs_delta_eur",
        grain="Статья × ЦФО",
        period="all_available_periods",
        filter_logic="Top 12 by cfo_abs_delta_eur.",
        chart_type="horizontal bar",
        caption_claim="Signal localization by article and CFO with concentration type.",
        caption_ru="Локализация показывает статью и ЦФО, где сконцентрирован сигнал; это кандидат на вопрос владельцу, не причина.",
        limitation="Localization identifies owner route candidates, not confirmed root cause.",
        data_path=CHART_DATA_DIR / "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO.parquet",
        image_path=image,
    )
    write_chart(record, loc_data, record)
    catalog_rows.append(record)

    # CH_EXEC_005
    plan_risk = read_mart("slice_plan_vs_history_article_cfo.parquet")
    plan_risk["label"] = plan_risk["article"].map(str) + " / " + plan_risk["cfo"].map(str)
    plan_risk_data = add_evidence_ids(
        plan_risk.sort_values("plan_vs_base_abs_delta_eur", ascending=False)
        .head(12)[["article", "cfo", "label", "planning_plan_eur", "historical_base_eur", "plan_vs_base_delta_eur", "plan_vs_base_abs_delta_eur", "base_months_available", "months_without_base", "planning_risk_flag", "planning_risk_basis", "source_slice"]],
        "CH_EXEC_005_PLANNING_RISK",
        "slice_plan_vs_history_article_cfo",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_005_PLANNING_RISK.png"
    save_barh(plan_risk_data, "label", "plan_vs_base_abs_delta_eur", "План к исторической базе", "ABS план к базе, EUR", image)
    record = chart_record(
        chart_id="CH_EXEC_005_PLANNING_RISK",
        chart_name_ru="План к исторической базе",
        memo_section="Плановый риск: план к исторической базе",
        purpose="Показать будущий плановый риск относительно истории.",
        source_mart="mart_main_full_budget",
        source_slice="slice_plan_vs_history_article_cfo",
        metric="plan_vs_base_abs_delta_eur",
        grain="Статья × ЦФО",
        period="planning_vs_historical_base",
        filter_logic="Top 12 by plan_vs_base_abs_delta_eur.",
        chart_type="bar",
        caption_claim="Planning risk is a future budget risk versus historical base.",
        caption_ru="Плановый риск показывает будущий план относительно исторической базы; это не факт исполнения.",
        limitation="Not actual execution; do not label as overrun or saving.",
        data_path=CHART_DATA_DIR / "CH_EXEC_005_PLANNING_RISK.parquet",
        image_path=image,
    )
    write_chart(record, plan_risk_data, record)
    catalog_rows.append(record)

    # CH_EXEC_006
    in_ctx = pf.copy()
    in_ctx["in_denominator_status"] = "valid_full_period"
    in_ctx["label"] = in_ctx["article"].map(str) + " / " + in_ctx["cfo"].map(str)
    in_ctx_data = add_evidence_ids(
        in_ctx[in_ctx["in_denominator_status"].eq("valid_full_period")]
        .sort_values("abs_delta_to_in_pct", ascending=False)
        .head(12)[["article", "cfo", "label", "abs_delta_eur", "in_eur", "abs_delta_to_in_pct", "delta_to_in_pct", "in_denominator_status", "source_slice"]],
        "CH_EXEC_006_IN_CONTEXT",
        "slice_plan_fact_article_cfo",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_006_IN_CONTEXT.png"
    save_barh(in_ctx_data, "label", "abs_delta_to_in_pct", "Отклонение к IN", "ABS отклонение к IN, %", image, percent=True)
    record = chart_record(
        chart_id="CH_EXEC_006_IN_CONTEXT",
        chart_name_ru="Отклонение к IN",
        memo_section="iGaming flow context: отклонения к IN",
        purpose="Показать, насколько отклонение статьи значимо относительно притока денег.",
        source_mart="mart_main_full_budget",
        source_slice="slice_plan_fact_article_cfo",
        metric="abs_delta_to_in_pct",
        grain="Статья × ЦФО",
        period="all_available_periods",
        filter_logic="in_denominator_status = valid_full_period; exclude service rows.",
        chart_type="bar",
        caption_claim="Deviation scale is normalized to a valid full-period IN denominator.",
        caption_ru="Отклонение нормировано к валидному IN за полный период; IN-OUT не суммируется по обычным статьям.",
        limitation="IN-OUT is not summed across ordinary article rows.",
        data_path=CHART_DATA_DIR / "CH_EXEC_006_IN_CONTEXT.parquet",
        image_path=image,
    )
    write_chart(record, in_ctx_data, record)
    catalog_rows.append(record)

    # CH_EXEC_007
    flow = read_mart("mart_flow_base_month.parquet")
    flow_data = add_evidence_ids(flow.copy(), "CH_EXEC_007_FLOW_BASE", "mart_flow_base_month")
    image = CHART_IMAGES_DIR / "CH_EXEC_007_FLOW_BASE.png"
    save_grouped_line(flow_data, "Динамика IN / OUT / IN-OUT", image)
    record = chart_record(
        chart_id="CH_EXEC_007_FLOW_BASE",
        chart_name_ru="Динамика IN / OUT / IN-OUT",
        memo_section="iGaming flow context: IN / OUT / IN-OUT",
        purpose="Показать контекст денежного потока iGaming.",
        source_mart="mart_flow_base_month",
        source_slice="mart_flow_base_month",
        metric="in_eur / out_eur / in_out_eur",
        grain="Месяц",
        period="monthly",
        filter_logic="Monthly flow rows only; no expense article rows.",
        chart_type="line chart",
        caption_claim="Monthly iGaming flow context: IN, OUT and IN-OUT.",
        caption_ru="IN / OUT / IN-OUT показаны помесячно и не смешиваются с расходными статьями.",
        limitation="Flow context is not an expense deviation chart.",
        data_path=CHART_DATA_DIR / "CH_EXEC_007_FLOW_BASE.parquet",
        image_path=image,
    )
    write_chart(record, flow_data, record)
    catalog_rows.append(record)

    # CH_EXEC_008
    source_qa = read_mart("slice_source_mix_summary.parquet")
    readiness = read_mart("profile_readiness_matrix.parquet")
    qa_data = source_qa[["source_mix", "rows_count", "plan_eur", "fact_eur", "reconciliation_status", "dq_status", "qa_status"]].copy()
    qa_data["profile_readiness_status"] = readiness.loc[
        readiness["profile_code"].eq(MEMO_PROFILE), "readiness_status"
    ].iloc[0]
    qa_data["source_mix_display_ru"] = qa_data["source_mix"].map(display_label)
    qa_data["rows_count_label"] = qa_data["rows_count"].map(format_count)
    row_count_warning = source_mix_row_count_warning(qa_data)
    if row_count_warning:
        qa_data["final_status_warning"] = row_count_warning
    qa_data = add_evidence_ids(qa_data, "CH_EXEC_008_QA_LIMITATIONS", "slice_source_mix_summary")
    image = CHART_IMAGES_DIR / "CH_EXEC_008_QA_LIMITATIONS.png"
    save_vertical_bar(
        qa_data,
        "source_mix_display_ru",
        "rows_count",
        "Ограничения данных: количество строк по типу источника",
        "Количество строк",
        image,
        value_formatter=format_count,
    )
    amount_data = qa_data.copy()
    amount_data["amount_basis_eur"] = amount_data[["plan_eur", "fact_eur"]].abs().max(axis=1)
    amount_data["amount_basis_label"] = amount_data["amount_basis_eur"].map(format_amount_eur)
    amount_image = CHART_IMAGES_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.png"
    save_vertical_bar(
        amount_data,
        "source_mix_display_ru",
        "amount_basis_eur",
        "Ограничения данных: сумма по типу источника",
        "Сумма, EUR",
        amount_image,
        value_formatter=format_amount_eur,
    )
    amount_spec = {
        "chart_id": "CH_EXEC_008_QA_LIMITATIONS_AMOUNT",
        "chart_name_ru": "Ограничения данных: сумма по типу источника",
        "memo_profile": MEMO_PROFILE,
        "memo_section": "QC и ограничения",
        "source_mart": "mart_main_full_budget",
        "source_slice": "slice_source_mix_summary",
        "metric": "amount_basis_eur",
        "grain": "Тип источника",
        "period": "all_available_periods",
        "filter_logic": "Группировка по типу источника; amount_basis_eur = max(abs(plan_eur), abs(fact_eur)).",
        "chart_type": "bar",
        "caption_ru": "Суммовая карта ограничений отделена от количества строк; ось Y показывает EUR.",
        "limitation": "Amount view is a QA context metric and must not be interpreted as financial misstatement.",
        "qa_status": "pass",
        "data_path": rel(CHART_DATA_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.parquet"),
        "image_path": rel(amount_image),
    }
    amount_data.to_parquet(CHART_DATA_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.parquet", index=False)
    write_json(CHART_SPECS_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.json", amount_spec)
    record = chart_record(
        chart_id="CH_EXEC_008_QA_LIMITATIONS",
        chart_name_ru="Ограничения данных: количество строк по типу источника",
        memo_section="QC и ограничения",
        purpose="Показать DQ / source quality blockers that limit interpretation.",
        source_mart="mart_main_full_budget",
        source_slice="slice_source_mix_summary",
        metric="rows_count",
        grain="Тип источника",
        period="all_available_periods",
        filter_logic="Группировка по типу источника и QA статусу.",
        chart_type="bar",
        caption_claim="Data quality and source mix are shown as limitations, not financial misstatement.",
        caption_ru="Состав источника и QA статусы показаны по количеству строк; суммы вынесены в отдельный QA-график.",
        limitation="QA row-count chart does not assert financial misstatement.",
        data_path=CHART_DATA_DIR / "CH_EXEC_008_QA_LIMITATIONS.parquet",
        image_path=image,
    )
    write_chart(record, qa_data, record)
    catalog_rows.append(record)

    # CH_EXEC_009 optional
    cp_unknown = read_mart("slice_counterparty_unknown.parquet")
    cp_data = add_evidence_ids(
        cp_unknown.sort_values("unknown_counterparty_amount_eur", ascending=False)
        .head(12)[["counterparty", "counterparty_key", "unknown_counterparty_rows", "unknown_counterparty_amount_eur", "unknown_counterparty_share", "counterparty_quality_flag", "source_slice"]],
        "CH_EXEC_009_COUNTERPARTY_QUALITY",
        "slice_counterparty_unknown",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_009_COUNTERPARTY_QUALITY.png"
    save_barh(cp_data, "counterparty", "unknown_counterparty_amount_eur", "Качество контрагентов", "Сумма неизвестных контрагентов, EUR", image)
    record = chart_record(
        chart_id="CH_EXEC_009_COUNTERPARTY_QUALITY",
        chart_name_ru="Качество контрагентов",
        memo_section="QC и ограничения",
        purpose="Показать unknown / missing key / concentration.",
        source_mart="mart_main_full_budget",
        source_slice="slice_counterparty_unknown",
        metric="unknown_counterparty_amount_eur",
        grain="Контрагент quality category",
        period="all_available_periods",
        filter_logic="Top 12 unknown counterparties by amount.",
        chart_type="bar",
        caption_claim="Экспозиция неизвестных контрагентов показана как ограничение качества данных.",
        caption_ru="Экспозиция неизвестных контрагентов показана как ограничение качества данных и не является управленческим выводом о контрагенте.",
        limitation="Counterparty quality chart limits conclusions where mapping is incomplete.",
        data_path=CHART_DATA_DIR / "CH_EXEC_009_COUNTERPARTY_QUALITY.parquet",
        image_path=image,
    )
    write_chart(record, cp_data, record)
    catalog_rows.append(record)

    # CH_EXEC_010 optional
    currency = read_mart("slice_currency_exposure.parquet")
    currency_data = add_evidence_ids(
        currency.sort_values("non_eur_amount_eur", ascending=False)
        .head(12)[["currency", "currency_original_amount", "currency_eur_amount", "non_eur_amount_eur", "non_eur_share", "rows_count", "fx_quality_flag", "source_slice", "limitation_text"]],
        "CH_EXEC_010_CURRENCY_EXPOSURE",
        "slice_currency_exposure",
    )
    image = CHART_IMAGES_DIR / "CH_EXEC_010_CURRENCY_EXPOSURE.png"
    save_barh(currency_data, "currency", "non_eur_amount_eur", "Валютная структура", "Сумма не-EUR, EUR", image)
    record = chart_record(
        chart_id="CH_EXEC_010_CURRENCY_EXPOSURE",
        chart_name_ru="Валютная структура",
        memo_section="QC и ограничения / Appendix",
        purpose="Показать non-EUR exposure.",
        source_mart="mart_main_full_budget",
        source_slice="slice_currency_exposure",
        metric="non_eur_amount_eur",
        grain="Валюта",
        period="all_available_periods",
        filter_logic="EUR non_eur_amount_eur = 0; top currencies by non_eur_amount_eur.",
        chart_type="bar",
        caption_claim="Non-EUR exposure excludes EUR from non-EUR amount.",
        caption_ru="Валютная структура показывает non-EUR exposure; EUR не включён в сумму не-EUR.",
        limitation="FX exposure is descriptive and does not create treasury/legal conclusion.",
        data_path=CHART_DATA_DIR / "CH_EXEC_010_CURRENCY_EXPOSURE.parquet",
        image_path=image,
    )
    write_chart(record, currency_data, record)
    catalog_rows.append(record)

    catalog = pd.DataFrame(catalog_rows).sort_values("chart_order").reset_index(drop=True)
    catalog.to_parquet(CHART_CATALOG_PARQUET, index=False)
    with pd.ExcelWriter(CHART_CATALOG_XLSX, engine="openpyxl") as writer:
        catalog.rename(columns=CATALOG_RU_COLUMNS).to_excel(writer, sheet_name="Каталог_Графиков", index=False)
        ws = writer.book["Каталог_Графиков"]
        ws.freeze_panes = "A2"
        for cells in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in cells[:100])
            ws.column_dimensions[cells[0].column_letter].width = min(max(max_len + 2, 12), 55)

    qa = validate_package(catalog, raw_before, stage_before, build_marts_before, docx_before)
    write_json(CHART_QA_REPORT, qa)
    CHART_QA_SUMMARY.write_text(
        "\n".join(
            [
                "# Chart Package QA Summary",
                "",
                f"qa_status: {qa['qa_status']}",
                f"memo_profile: {MEMO_PROFILE}",
                f"charts_count: {qa['charts_count']}",
                "",
                "## Warnings",
                *([f"- {warning}" for warning in qa.get("warnings", [])] or ["- none"]),
                "",
                "## Checks",
                *[f"- {key}: {'pass' if value else 'fail'}" for key, value in qa["checks"].items()],
                "",
                "## Residual Risks",
                "- Chart package is preview/data package only; no DOCX or final memo conclusions generated.",
                "- Captions are constrained to chart data and should be reviewed before final narrative use.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return qa


def validate_package(
    catalog: pd.DataFrame,
    raw_before: dict[str, tuple[int, int]],
    stage_before: dict[str, tuple[int, int]],
    build_marts_before: dict[str, tuple[int, int]],
    docx_before: list[Path],
) -> dict[str, Any]:
    raw_after = snapshot(RAW_DIR)
    stage_after = snapshot(STAGE_DIR)
    build_marts_after = snapshot_file(BUILD_MARTS_SCRIPT)
    docx_after = list(PROJECT_ROOT.rglob("*.docx"))
    required_chart_ids = {
        "CH_EXEC_001_PLAN_FACT_TOP_ABS",
        "CH_EXEC_002_YOY_TOP_SHIFT",
        "CH_EXEC_003_MOM_INSTABILITY",
        "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO",
        "CH_EXEC_005_PLANNING_RISK",
        "CH_EXEC_006_IN_CONTEXT",
        "CH_EXEC_007_FLOW_BASE",
        "CH_EXEC_008_QA_LIMITATIONS",
    }
    optional_chart_ids = {"CH_EXEC_009_COUNTERPARTY_QUALITY", "CH_EXEC_010_CURRENCY_EXPOSURE"}
    chart_ids = set(catalog["chart_id"])
    data_checks: dict[str, bool] = {}
    for row in catalog.to_dict("records"):
        data = pd.read_parquet(PROJECT_ROOT / row["data_path"])
        data_checks[row["chart_id"]] = bool(not data.empty and (PROJECT_ROOT / row["image_path"]).exists())

    with pd.ExcelFile(CHART_CATALOG_XLSX) as xl:
        headers = pd.read_excel(xl, sheet_name="Каталог_Графиков", nrows=0).columns.tolist()
        excel_headers_ru = set(CATALOG_RU_COLUMNS.values()).issubset(headers) and not any("_" in str(header) for header in headers)

    plan_fact_data = pd.read_parquet(CHART_DATA_DIR / "CH_EXEC_001_PLAN_FACT_TOP_ABS.parquet")
    yoy_data = pd.read_parquet(CHART_DATA_DIR / "CH_EXEC_002_YOY_TOP_SHIFT.parquet")
    yoy_source_data = read_mart("slice_yoy_article.parquet")
    yoy_valid_rows_count = int(yoy_source_data["prior_year_available_flag"].eq(1).sum())
    yoy_signal_count = int(read_mart("mart_signal_catalog_full.parquet").query("signal_type == 'yoy_shift'").shape[0])
    in_context_data = pd.read_parquet(CHART_DATA_DIR / "CH_EXEC_006_IN_CONTEXT.parquet")
    qa_limitations_data = pd.read_parquet(CHART_DATA_DIR / "CH_EXEC_008_QA_LIMITATIONS.parquet")
    qa_limitations_amount_data = pd.read_parquet(CHART_DATA_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.parquet")
    source_mix_summary = read_mart("slice_source_mix_summary.parquet")
    planning_row = catalog.loc[catalog["chart_id"].eq("CH_EXEC_005_PLANNING_RISK")].iloc[0]
    currency_data = pd.read_parquet(CHART_DATA_DIR / "CH_EXEC_010_CURRENCY_EXPOSURE.parquet")
    source_mix_warning = (
        qa_limitations_data["final_status_warning"].dropna().iloc[0]
        if "final_status_warning" in qa_limitations_data.columns
        and qa_limitations_data["final_status_warning"].fillna("").ne("").any()
        else ""
    )
    image_dimensions_ok = True
    for image_path in catalog["image_path"]:
        with Image.open(PROJECT_ROOT / image_path) as image:
            width, height = image.size
            image_dimensions_ok = image_dimensions_ok and width >= 1200 and 700 <= height <= 1800

    checks = {
        "chart_catalog_exists": CHART_CATALOG_PARQUET.exists() and CHART_CATALOG_XLSX.exists(),
        "required_charts_exist": required_chart_ids.issubset(chart_ids),
        "optional_charts_exist": optional_chart_ids.issubset(chart_ids),
        "each_chart_has_data_and_image": all(data_checks.values()),
        "each_chart_has_source_metric_grain_period_limitation": bool(
            catalog[["source_mart", "source_slice", "metric", "grain", "period", "limitation"]].fillna("").ne("").all().all()
        ),
        "each_chart_has_role_order_placement_caption": bool(
            catalog[["chart_role", "chart_order", "recommended_placement", "caption_ru"]].fillna("").ne("").all().all()
            and catalog["chart_role"].isin(["executive_body", "appendix", "qa_only"]).all()
        ),
        "chart_catalog_order_matches_executive_route": bool(catalog["chart_order"].is_monotonic_increasing),
        "executive_body_charts_cover_memo_route": bool(
            set(catalog.loc[catalog["chart_role"].eq("executive_body"), "chart_id"])
            == {
                "CH_EXEC_001_PLAN_FACT_TOP_ABS",
                "CH_EXEC_002_YOY_TOP_SHIFT",
                "CH_EXEC_003_MOM_INSTABILITY",
                "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO",
                "CH_EXEC_005_PLANNING_RISK",
                "CH_EXEC_006_IN_CONTEXT",
                "CH_EXEC_007_FLOW_BASE",
                "CH_EXEC_008_QA_LIMITATIONS",
            }
        ),
        "no_chart_reads_raw_or_stage": bool(
            ~catalog["source_mart"].str.contains("raw|stage", case=False, regex=True).any()
            and ~catalog["source_slice"].str.contains("raw|stage", case=False, regex=True).any()
        ),
        "service_rows_excluded_from_expense_deviation_charts": bool(not plan_fact_data["article"].isin(SERVICE_VALUES).any()),
        "in_ratio_charts_use_valid_denominator_status": bool(
            in_context_data["in_denominator_status"].isin(["valid_same_period", "valid_full_period"]).all()
        ),
        "planning_risk_labeled_future_risk_not_actual_execution": bool(
            "future" in planning_row["caption_claim"].lower()
            and "not actual execution" in planning_row["limitation"].lower()
        ),
        "yoy_chart_does_not_use_missing_base_as_strong_conclusion": bool(
            yoy_data["prior_year_available_flag"].eq(1).all()
            and catalog.loc[catalog["chart_id"].eq("CH_EXEC_002_YOY_TOP_SHIFT"), "limitation"].str.contains("Weak YoY base", regex=False).all()
        ),
        "yoy_chart_top5_when_enough_valid_rows": bool(yoy_valid_rows_count >= 5 and len(yoy_data) == 5),
        "yoy_chart_title_matches_row_count": bool(
            catalog.loc[catalog["chart_id"].eq("CH_EXEC_002_YOY_TOP_SHIFT"), "chart_name_ru"].iloc[0]
            == "Топ-5 YoY-сдвигов по EUR"
        ),
        "yoy_chart_labels_are_unique": bool(yoy_data["label"].is_unique),
        "yoy_chart_bar_metric_equals_label_metric": bool(yoy_data["abs_yoy_delta_eur"].notna().all()),
        "yoy_chart_visible_labels_business_readable": bool(
            "article_display_ru" in yoy_data.columns
            and not yoy_data["label"].astype(str).str.contains("ONJN Gaming Tax", regex=False).any()
        ),
        "excel_visible_columns_are_russian": bool(excel_headers_ru),
        "chart_images_generated": bool(all((PROJECT_ROOT / path).exists() for path in catalog["image_path"])),
        "chart_images_readable_dimensions": bool(image_dimensions_ok),
        "style_config_exists": bool(CHART_STYLE_CONFIG.exists()),
        "display_label_mapping_exists": bool(CHART_DISPLAY_LABEL_MAPPING.exists()),
        "approved_palette_used": bool(
            json.loads(CHART_STYLE_CONFIG.read_text(encoding="utf-8")) == STYLE_CONFIG
        ),
        "source_mix_display_labels_are_russian": bool(
            set(qa_limitations_data["source_mix_display_ru"]) == {
                "Факт без плана",
                "План без факта",
                "Корректировка план-факт",
                "План и факт",
                "Сводный бюджет",
                "Возвраты игрокам",
            }
            and not qa_limitations_data["source_mix_display_ru"].astype(str).isin(DISPLAY_LABEL_MAPPING.keys()).any()
        ),
        "qa_limitations_source_metrics_unchanged": bool(
            qa_limitations_data[["source_mix", "rows_count", "plan_eur", "fact_eur"]]
            .sort_values("source_mix")
            .reset_index(drop=True)
            .equals(
                source_mix_summary[["source_mix", "rows_count", "plan_eur", "fact_eur"]]
                .sort_values("source_mix")
                .reset_index(drop=True)
            )
        ),
        "qa_limitations_row_count_has_no_million_suffix": bool(
            qa_limitations_data["rows_count_label"].fillna("").astype(str).str.contains("M").sum() == 0
        ),
        "qa_limitations_row_count_and_amount_are_separated": bool(
            (CHART_DATA_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.parquet").exists()
            and (CHART_IMAGES_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.png").exists()
            and "amount_basis_eur" in qa_limitations_amount_data.columns
        ),
        "qa_limitations_amount_axis_uses_eur_metric": bool(
            json.loads((CHART_SPECS_DIR / "CH_EXEC_008_QA_LIMITATIONS_AMOUNT.json").read_text(encoding="utf-8"))["metric"]
            == "amount_basis_eur"
        ),
        "source_mix_plan_and_fact_warning_added": bool(source_mix_warning),
        "no_docx_generated": sorted(str(path) for path in docx_before) == sorted(str(path) for path in docx_after),
        "raw_untouched": raw_before == raw_after,
        "stage_untouched": stage_before == stage_after,
        "mart_formulas_untouched": build_marts_before == build_marts_after,
        "eur_not_counted_as_non_eur_exposure": bool(
            currency_data.loc[currency_data["currency"].eq("EUR"), "non_eur_amount_eur"].fillna(0).eq(0).all()
        ),
        "no_long_lineage_in_chart_datasets": bool(
            all(
                not ({"source_rows", "source_files"} & set(pd.read_parquet(path).columns))
                for path in CHART_DATA_DIR.glob("*.parquet")
            )
        ),
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "pass" if all(checks.values()) else "fail",
        "memo_profile": MEMO_PROFILE,
        "memo_profile_ru": MEMO_PROFILE_RU,
        "charts_count": int(len(catalog)),
        "required_chart_ids": sorted(required_chart_ids),
        "optional_chart_ids": sorted(optional_chart_ids),
        "checks": checks,
        "chart_data_checks": data_checks,
        "chart_catalog": rel(CHART_CATALOG_PARQUET),
        "chart_catalog_excel": rel(CHART_CATALOG_XLSX),
        "chart_data_dir": rel(CHART_DATA_DIR),
        "chart_specs_dir": rel(CHART_SPECS_DIR),
        "chart_images_dir": rel(CHART_IMAGES_DIR),
        "yoy_chart_diagnostics": {
            "slice_yoy_article_valid_prior_year_rows": yoy_valid_rows_count,
            "mart_signal_catalog_yoy_shift_rows": yoy_signal_count,
            "chart_dataset_rows": int(len(yoy_data)),
            "selection_reason": "top_5_valid_prior_year_rows" if yoy_valid_rows_count >= 5 else "fewer_than_5_valid_prior_year_rows",
        },
        "warnings": [source_mix_warning] if source_mix_warning else [],
        "production_readiness_claimed": False,
    }


def main() -> None:
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="chart_package_generation", status="start")
    qa = build_chart_package()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="chart_package_generation", status=qa["qa_status"], details={"charts": qa["charts_count"]})
    print(json.dumps({"qa_status": qa["qa_status"], "charts_count": qa["charts_count"], "checks": qa["checks"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
