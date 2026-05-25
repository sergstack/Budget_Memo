from __future__ import annotations

import csv
import re
import tempfile
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_ROOT = PROJECT_ROOT / "01_raw"
STAGE_DIR = PROJECT_ROOT / "02_stage"
AUDIT_DIR = STAGE_DIR / "audit"

BUDGET_ROWS_DIR = RAW_ROOT / "budget_rows"
DDS_DIR = RAW_ROOT / "dds"
P_FACT_DIR = RAW_ROOT / "p-fact"
DDS_ARTICLE_PATH = RAW_ROOT / "dds article" / "dds_article.xlsx"
CONS_BUDGET_PATH = RAW_ROOT / "cons_budget" / "cons_budget.xlsx"

FULL_STAGE_OUTPUT = STAGE_DIR / "01_full_stage.csv"
DIAGNOSTIC_OUTPUTS = {
    "p_fact": AUDIT_DIR / "01_p_fact.csv",
    "budget_rows": AUDIT_DIR / "02_budget_rows.csv",
    "dds": AUDIT_DIR / "03_dds.csv",
    "p_fact_adjustments": AUDIT_DIR / "04_p_fact_adjustments.csv",
    "cons_budget": AUDIT_DIR / "05_cons_budget.csv",
}
OLD_DIAGNOSTIC_OUTPUTS = [
    STAGE_DIR / "90_p_fact_stage.csv",
    STAGE_DIR / "91_budget_rows_stage.csv",
    STAGE_DIR / "92_dds_stage.csv",
    STAGE_DIR / "93_p_fact_adjustments_stage.csv",
    STAGE_DIR / "94_cons_budget_stage.csv",
]
OLD_USER_OUTPUTS = [
    STAGE_DIR / "01_article_month.csv",
    STAGE_DIR / "02_article_cfo_counterparty_month.csv",
]

P_FACT_COLUMNS = [
    "Код статьи ДДС",
    "Статья ДДС",
    "План периода",
    "План",
    "Факт",
    "План - Факт",
    "% исполнения бюджета",
]

MISSING_COUNTERPARTY = "Контрагент не указан"
TOLERANCE = 0.01
ACTUALS_CLOSED_THROUGH_MONTH = "2026-04"
FULL_STAGE_COLUMNS = [
    "Месяц",
    "Дата",
    "Тип периода",
    "source_mix",
    "included_in_reconciliation",
    "has_plan",
    "has_fact",
    "has_p_fact_adjustment",
    "has_player_refund",
    "Код статьи ДДС",
    "Тип",
    "Статья 1",
    "Статья 2",
    "Статья",
    "ЦФО",
    "Юр. лицо",
    "Контрагент",
    "Ключ контрагента",
    "Тип контрагента",
    "Валюта",
    "Сумма исходная",
    "План, EUR",
    "Факт, EUR",
    "IN-OUT, EUR",
    "source_file",
    "source_row_id",
]


def clean_xlsx_for_reader(src: Path, dst: Path) -> None:
    with ZipFile(src, "r") as zin, ZipFile(dst, "w", ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            data = zin.read(item.filename)
            if item.filename.startswith("xl/worksheets/") and item.filename.endswith(".xml"):
                data = re.sub(rb'\s+showZeroes="[^"]*"', b"", data)
            zout.writestr(item, data)


def read_xlsx(path: Path, tmp_path: Path, **kwargs) -> pd.DataFrame:
    clean_path = tmp_path / path.name
    clean_xlsx_for_reader(path, clean_path)
    return pd.read_excel(clean_path, sheet_name=0, **kwargs)


def month_from_filename(path: Path) -> str:
    match = re.search(r"(\d{4}-\d{2})", path.name)
    if not match:
        raise ValueError(f"Cannot extract month from file name: {path.name}")
    return match.group(1)


def classify_period_month(period_month: str, actuals_closed_through_month: str = ACTUALS_CLOSED_THROUGH_MONTH) -> str:
    month = pd.Period(str(period_month), freq="M")
    cutoff = pd.Period(str(actuals_closed_through_month), freq="M")
    return "historical" if month <= cutoff else "planning"


def classify_period_series(
    period_month: pd.Series,
    actuals_closed_through_month: str = ACTUALS_CLOSED_THROUGH_MONTH,
) -> pd.Series:
    cutoff = pd.Period(str(actuals_closed_through_month), freq="M")
    months = pd.PeriodIndex(period_month.astype(str), freq="M")
    return pd.Series(np.where(months <= cutoff, "historical", "planning"), index=period_month.index)


def norm_text(series: pd.Series) -> pd.Series:
    return (
        series.fillna("")
        .astype(str)
        .str.replace("–", "-", regex=False)
        .str.replace("—", "-", regex=False)
        .str.split()
        .str.join(" ")
        .str.strip()
    )


def to_number(series: pd.Series) -> pd.Series:
    return pd.to_numeric(
        series.astype(str)
        .str.replace("%", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.replace(",", ".", regex=False)
        .replace({"": np.nan, "nan": np.nan, "None": np.nan}),
        errors="coerce",
    )


def extract_code(series: pd.Series) -> pd.Series:
    return series.astype(str).str.extract(r"(CF\d{7})", expand=False)


def extract_name(series: pd.Series) -> pd.Series:
    return series.astype(str).str.replace(r"CF\d{7}\s*[-–—]?\s*", "", regex=True).str.strip()


def normalize_counterparty(series: pd.Series) -> pd.Series:
    return norm_text(series).replace({"": MISSING_COUNTERPARTY, "-": MISSING_COUNTERPARTY})


def format_date(series: pd.Series) -> pd.Series:
    return pd.to_datetime(series, errors="coerce").dt.strftime("%Y-%m-%d")


def read_budget_raw(tmp_path: Path) -> list[tuple[str, pd.DataFrame]]:
    frames = []
    for path in sorted(BUDGET_ROWS_DIR.glob("raw_*.xlsx")):
        frames.append((month_from_filename(path), read_xlsx(path, tmp_path)))
    if not frames:
        raise FileNotFoundError(f"No raw_*.xlsx files found in {BUDGET_ROWS_DIR}")
    return frames


def build_p_fact(tmp_path: Path) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    for source_path in sorted(P_FACT_DIR.glob("p-fact_*.xlsx")):
        month = month_from_filename(source_path)
        raw = pd.read_excel(source_path, sheet_name=0, header=None)
        frame = raw.iloc[2:].reset_index(drop=True).dropna(axis=1, how="all")
        if frame.shape[1] != len(P_FACT_COLUMNS):
            raise ValueError(f"{source_path.name}: expected 7 columns, got {frame.shape[1]}")
        frame.columns = P_FACT_COLUMNS
        frame.insert(0, "Месяц", month)
        frame["Статья ДДС"] = norm_text(frame["Статья ДДС"])
        frame["ЦФО"] = np.where(frame["Статья ДДС"].eq(""), frame["Код статьи ДДС"], np.nan)
        frame["ЦФО"] = (
            pd.Series(frame["ЦФО"])
            .ffill()
            .fillna("")
            .astype(str)
            .str.replace("ЦФО: ", "", regex=False)
            .str.strip()
        )
        frame["Код статьи ДДС"] = frame["Код статьи ДДС"].astype(str)
        frame = frame[frame["Код статьи ДДС"].str.startswith("CF")].copy()
        frame["План"] = to_number(frame["План"]).fillna(0.0)
        frame["Факт"] = to_number(frame["Факт"]).fillna(0.0)
        frames.append(frame[["Месяц", "ЦФО", "Код статьи ДДС", "Статья ДДС", "План", "Факт"]])

    if not frames:
        raise FileNotFoundError(f"No p-fact_*.xlsx files found in {P_FACT_DIR}")
    return pd.concat(frames, ignore_index=True)


def build_budget_rows(
    budget_raw: list[tuple[str, pd.DataFrame]],
    valid_triples_df: pd.DataFrame,
    valid_pairs_df: pd.DataFrame,
    p_fact_months: set[str],
) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    required = ["ЦФО", "Статья ДДС", "Сумма, EUR", "Контрагент", "Период", "Комментарий", "Дата оплаты"]

    for month, frame in budget_raw:
        missing = [col for col in required if col not in frame.columns]
        if missing:
            raise ValueError(f"budget_rows {month}: missing columns {missing}")
        optional = ["Юр. лицо", "Валюта", "Сумма"]
        part = frame[required + [col for col in optional if col in frame.columns]].copy()
        part["source_file"] = f"raw_{month}.xlsx"
        part["source_row_id"] = part.index + 2
        part.insert(0, "Месяц", month)
        part["ЦФО"] = norm_text(part["ЦФО"])
        part["Код статьи ДДС"] = extract_code(part["Статья ДДС"])
        part["Статья ДДС"] = extract_name(part["Статья ДДС"])
        is_historical = classify_period_series(part["Месяц"]).eq("historical")
        part_historical = part[is_historical].merge(valid_triples_df, on=["Месяц", "ЦФО", "Код статьи ДДС"], how="inner")
        part_planning = part[~is_historical].merge(valid_pairs_df, on=["ЦФО", "Код статьи ДДС"], how="inner")
        part = pd.concat([part_historical, part_planning], ignore_index=True)
        part["Сумма (план)"] = to_number(part["Сумма, EUR"]).fillna(0.0)
        part["Сумма (факт)"] = 0.0
        part["Контрагент"] = normalize_counterparty(part["Контрагент"])
        part["Тип операции"] = "План"
        part["Дата"] = format_date(part["Дата оплаты"])
        part["Тип периода"] = classify_period_series(part["Месяц"])
        part["Источник данных"] = "budget_rows"
        part["Юр. лицо"] = part["Юр. лицо"] if "Юр. лицо" in part.columns else ""
        part["Тип контрагента"] = ""
        part["Валюта"] = part["Валюта"] if "Валюта" in part.columns else ""
        part["Сумма исходная"] = part["Сумма"] if "Сумма" in part.columns else part["Сумма, EUR"]
        part["is_player_refund"] = 0
        part["included_in_reconciliation"] = 1
        frames.append(
            part[
                [
                    "Месяц",
                    "Дата",
                    "Тип периода",
                    "Источник данных",
                    "ЦФО",
                    "Код статьи ДДС",
                    "Статья ДДС",
                    "Тип операции",
                    "Сумма (план)",
                    "Сумма (факт)",
                    "Юр. лицо",
                    "Контрагент",
                    "Тип контрагента",
                    "Валюта",
                    "Сумма исходная",
                    "included_in_reconciliation",
                    "is_player_refund",
                    "source_file",
                    "source_row_id",
                ]
            ]
        )

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_dds(tmp_path: Path, valid_triples_df: pd.DataFrame) -> pd.DataFrame:
    frames: list[pd.DataFrame] = []
    required = ["ЦФО", "Статья ДДС", "Сумма, EUR", "Дата начисления", "Тип контрагента"]

    for source_path in sorted(DDS_DIR.glob("dds_*.xlsx")):
        month = month_from_filename(source_path)
        frame = read_xlsx(source_path, tmp_path)
        missing = [col for col in required if col not in frame.columns]
        if missing:
            raise ValueError(f"dds {month}: missing columns {missing}")

        optional = ["Юр. лицо", "Валюта", "Сумма"]
        part = frame[required + [col for col in optional if col in frame.columns]].copy()
        part["source_file"] = source_path.name
        part["source_row_id"] = part.index + 2
        part.insert(0, "Месяц", month)
        if "КА-получатель" in frame.columns:
            part["Контрагент"] = frame["КА-получатель"]
        else:
            part["Контрагент"] = ""
        if "Получатель - Контрагент" in frame.columns:
            missing_counterparty = norm_text(part["Контрагент"]).eq("")
            part.loc[missing_counterparty, "Контрагент"] = frame.loc[missing_counterparty, "Получатель - Контрагент"]

        part["ЦФО"] = norm_text(part["ЦФО"])
        part["Код статьи ДДС"] = extract_code(part["Статья ДДС"])
        part["Статья ДДС"] = extract_name(part["Статья ДДС"])
        part["Сумма (план)"] = 0.0
        part["Сумма (факт)"] = to_number(part["Сумма, EUR"]).fillna(0.0)
        part["Контрагент"] = normalize_counterparty(part["Контрагент"])
        accrual_month = pd.to_datetime(part["Дата начисления"], errors="coerce").dt.strftime("%Y-%m")
        part = part[accrual_month.eq(month)].copy()
        part = part.merge(valid_triples_df, on=["Месяц", "ЦФО", "Код статьи ДДС"], how="inner")
        is_player_refund = (
            part["Код статьи ДДС"].eq("CF4030400")
            & part["Тип контрагента"].astype(str).eq("Покупатель / Customer")
        )
        part["Тип операции"] = np.where(is_player_refund, "Возврат", "Факт")
        part["Дата"] = format_date(part["Дата начисления"])
        part["Тип периода"] = classify_period_month(month)
        part["Источник данных"] = "dds"
        part["Юр. лицо"] = part["Юр. лицо"] if "Юр. лицо" in part.columns else ""
        part["Валюта"] = part["Валюта"] if "Валюта" in part.columns else ""
        part["Сумма исходная"] = part["Сумма"] if "Сумма" in part.columns else part["Сумма, EUR"]
        part["is_player_refund"] = is_player_refund.astype(int)
        part["included_in_reconciliation"] = np.where(is_player_refund, 0, 1)
        frames.append(
            part[
                [
                    "Месяц",
                    "Дата",
                    "Тип периода",
                    "Источник данных",
                    "ЦФО",
                    "Код статьи ДДС",
                    "Статья ДДС",
                    "Тип операции",
                    "Сумма (план)",
                    "Сумма (факт)",
                    "Юр. лицо",
                    "Контрагент",
                    "Тип контрагента",
                    "Валюта",
                    "Сумма исходная",
                    "included_in_reconciliation",
                    "is_player_refund",
                    "source_file",
                    "source_row_id",
                ]
            ]
        )

    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()


def build_article_reference(budget_raw: list[tuple[str, pd.DataFrame]], raw_art: pd.DataFrame) -> pd.DataFrame:
    article = (
        raw_art[["Код", "Тип", "Направление", "Название"]]
        .rename(columns={"Код": "Код статьи ДДС", "Тип": "Тип статьи", "Название": "Название статьи"})
        .drop_duplicates("Код статьи ДДС")
    )

    hierarchy_frames: list[pd.DataFrame] = []
    hierarchy_cols = ["Статья ДДС 1", "Статья ДДС 2", "Статья ДДС 3"]
    for _, frame in budget_raw:
        if not {"Статья ДДС", *hierarchy_cols}.issubset(frame.columns):
            continue
        part = frame[["Статья ДДС", *hierarchy_cols]].copy()
        part["Код статьи ДДС"] = extract_code(part["Статья ДДС"])
        hierarchy_frames.append(part[["Код статьи ДДС", *hierarchy_cols]])

    if hierarchy_frames:
        hierarchy = (
            pd.concat(hierarchy_frames, ignore_index=True)
            .dropna(subset=["Код статьи ДДС"])
            .drop_duplicates("Код статьи ДДС")
        )
    else:
        hierarchy = pd.DataFrame(columns=["Код статьи ДДС", *hierarchy_cols])

    ref = article.merge(hierarchy, on="Код статьи ДДС", how="left")
    ref["Статья 1"] = norm_text(ref["Статья ДДС 1"]).replace({"": np.nan})
    ref["Статья 2"] = norm_text(ref["Статья ДДС 2"]).replace({"": np.nan})
    third = norm_text(ref["Статья ДДС 3"]).replace({"": np.nan})
    article_name = norm_text(ref["Название статьи"]).replace({"": np.nan})
    ref["Статья"] = third.fillna(ref["Статья 2"]).fillna(ref["Статья 1"]).fillna(article_name)
    ref["Статья 1"] = ref["Статья 1"].fillna(article_name)
    ref["Статья 2"] = ref["Статья 2"].fillna(ref["Статья 1"])
    return ref[["Код статьи ДДС", "Тип статьи", "Направление", "Статья 1", "Статья 2", "Статья"]]


def apply_p_fact_adjustments(p_fact: pd.DataFrame, union_df: pd.DataFrame) -> pd.DataFrame:
    p_agg = p_fact.groupby(["Месяц", "ЦФО", "Код статьи ДДС"], as_index=False).agg(
        Статья_ДДС=("Статья ДДС", "first"),
        План_p_fact=("План", "sum"),
        Факт_p_fact=("Факт", "sum"),
    )
    u_agg = union_df[union_df["Тип операции"] != "Возврат"].groupby(
        ["Месяц", "ЦФО", "Код статьи ДДС"], as_index=False
    ).agg(
        План_union=("Сумма (план)", "sum"),
        Факт_union=("Сумма (факт)", "sum"),
    )
    adjustments = p_agg.merge(u_agg, on=["Месяц", "ЦФО", "Код статьи ДДС"], how="left")
    adjustments[["План_union", "Факт_union"]] = adjustments[["План_union", "Факт_union"]].fillna(0.0)
    adjustments["Сумма (план)"] = (adjustments["План_p_fact"] - adjustments["План_union"]).round(2)
    adjustments["Сумма (факт)"] = (adjustments["Факт_p_fact"] - adjustments["Факт_union"]).round(2)
    adjustments = adjustments[
        (adjustments["Сумма (план)"].abs() >= TOLERANCE)
        | (adjustments["Сумма (факт)"].abs() >= TOLERANCE)
    ].copy()

    if adjustments.empty:
        return union_df

    adjustment_rows = pd.DataFrame(
        {
            "Месяц": adjustments["Месяц"],
            "Дата": pd.to_datetime(adjustments["Месяц"] + "-01").dt.strftime("%Y-%m-%d"),
            "Тип периода": classify_period_series(adjustments["Месяц"]),
            "Источник данных": "p-fact_adjustment",
            "ЦФО": adjustments["ЦФО"],
            "Код статьи ДДС": adjustments["Код статьи ДДС"],
            "Статья ДДС": adjustments["Статья_ДДС"],
            "Тип операции": "Корректировка p-fact",
            "Сумма (план)": adjustments["Сумма (план)"],
            "Сумма (факт)": adjustments["Сумма (факт)"],
            "Юр. лицо": "",
            "Контрагент": "p-fact",
            "Тип контрагента": "",
            "Валюта": "EUR",
            "Сумма исходная": adjustments["Сумма (план)"] + adjustments["Сумма (факт)"],
            "included_in_reconciliation": 1,
            "is_player_refund": 0,
            "source_file": "p-fact",
            "source_row_id": (
                adjustments["Месяц"].astype(str)
                + "|"
                + adjustments["ЦФО"].astype(str)
                + "|"
                + adjustments["Код статьи ДДС"].astype(str)
            ),
        }
    )
    return pd.concat([union_df, adjustment_rows], ignore_index=True)


def build_reconciliation(p_fact: pd.DataFrame, union_df: pd.DataFrame) -> pd.DataFrame:
    keys = ["Месяц", "ЦФО", "Код статьи ДДС"]
    p_agg = p_fact.groupby(keys, as_index=False).agg(
        План_p_fact=("План", "sum"),
        Факт_p_fact=("Факт", "sum"),
    )
    u_agg = union_df[union_df["included_in_reconciliation"].eq(1)].groupby(keys, as_index=False).agg(
        План_union=("Сумма (план)", "sum"),
        Факт_union=("Сумма (факт)", "sum"),
    )
    recon = p_agg.merge(u_agg, on=keys, how="left")
    recon[["План_union", "Факт_union"]] = recon[["План_union", "Факт_union"]].fillna(0.0)
    recon["diff_plan"] = recon["План_union"] - recon["План_p_fact"]
    recon["diff_fact"] = recon["Факт_union"] - recon["Факт_p_fact"]
    recon["ok_plan"] = recon["diff_plan"].abs() <= TOLERANCE
    recon["ok_fact"] = recon["diff_fact"].abs() <= TOLERANCE
    return recon


def load_cons_budget(tmp_path: Path) -> pd.DataFrame:
    raw = read_xlsx(CONS_BUDGET_PATH, tmp_path, header=None)
    metric_rows = {"IN": 2, "OUT": 3, "IN-OUT": 6}
    records = []
    col = 7
    while col + 1 < raw.shape[1]:
        month_value = raw.iloc[0, col]
        if pd.isna(month_value):
            break
        month = str(month_value).strip()
        for metric, row_idx in metric_rows.items():
            records.append(
                {
                    "Месяц": month,
                    "metric": metric,
                    "План, EUR": raw.iloc[row_idx, col],
                    "Факт, EUR": raw.iloc[row_idx, col + 1],
                }
            )
        col += 2
    cons = pd.DataFrame(records)
    cons["План, EUR"] = to_number(cons["План, EUR"])
    cons["Факт, EUR"] = to_number(cons["Факт, EUR"])
    return cons


def split_counterparty(value: object) -> tuple[str, str]:
    text = "" if pd.isna(value) else str(value).strip()
    if text in {"", "-"}:
        return MISSING_COUNTERPARTY, "unknown"
    if "/" not in text:
        return text, "unknown"
    name, key = text.rsplit("/", 1)
    name = name.strip() or MISSING_COUNTERPARTY
    key = key.strip() or "unknown"
    return name, key


def join_unique(values: pd.Series) -> str:
    unique_values = []
    seen = set()
    for value in values:
        text = "" if pd.isna(value) else str(value).strip()
        if text and text not in seen:
            unique_values.append(text)
            seen.add(text)
    return " | ".join(unique_values)


def restore_fact_counterparty_keys_from_plan(stage: pd.DataFrame) -> pd.DataFrame:
    key_cols = ["Месяц", "ЦФО", "Код статьи ДДС", "Контрагент"]
    known_plan = stage[
        stage["Тип операции"].eq("План")
        & stage["Ключ контрагента"].ne("unknown")
        & stage["Ключ контрагента"].ne("p_fact")
    ]
    unique_plan_keys = (
        known_plan.groupby(key_cols, as_index=False, dropna=False)
        .agg(
            plan_key=("Ключ контрагента", "first"),
            plan_key_count=("Ключ контрагента", "nunique"),
        )
        .query("plan_key_count == 1")
    )
    if unique_plan_keys.empty:
        return stage

    restored = stage.merge(unique_plan_keys[key_cols + ["plan_key"]], on=key_cols, how="left")
    restore_mask = (
        restored["Тип операции"].eq("Факт")
        & restored["Ключ контрагента"].eq("unknown")
        & restored["plan_key"].notna()
    )
    restored.loc[restore_mask, "Ключ контрагента"] = restored.loc[restore_mask, "plan_key"]
    return restored.drop(columns=["plan_key"])


def classify_source_mix(row: pd.Series) -> str:
    has_plan = row["has_plan"] == 1
    has_fact = row["has_fact"] == 1
    has_adjustment = row["has_p_fact_adjustment"] == 1
    has_refund = row["has_player_refund"] == 1
    if has_refund and not (has_plan or has_fact or has_adjustment):
        return "refund_only"
    if has_refund:
        return "refund_mixed"
    if has_adjustment:
        return "p_fact_adjusted"
    if has_plan and has_fact:
        return "plan_and_fact"
    if has_plan:
        return "plan_only"
    if has_fact:
        return "fact_only"
    return "mixed"


def build_cons_budget_rows(cons_budget: pd.DataFrame, p_fact_months: set[str]) -> pd.DataFrame:
    rows = []
    for _, row in cons_budget.iterrows():
        metric = row["metric"]
        plan_value = row["План, EUR"]
        period_type = classify_period_month(row["Месяц"])
        fact_value = row["Факт, EUR"] if period_type == "historical" else np.nan
        rows.append(
            {
                "Месяц": row["Месяц"],
                "Дата": f"{row['Месяц']}-01",
                "Тип периода": period_type,
                "source_mix": "cons_budget",
                "included_in_reconciliation": 0,
                "has_plan": int(pd.notna(plan_value) and plan_value != 0),
                "has_fact": int(pd.notna(fact_value) and fact_value != 0),
                "has_p_fact_adjustment": 0,
                "has_player_refund": 0,
                "Код статьи ДДС": metric,
                "Тип": metric,
                "Статья 1": metric,
                "Статья 2": metric,
                "Статья": metric,
                "ЦФО": metric,
                "Юр. лицо": "not_applicable",
                "Контрагент": metric,
                "Ключ контрагента": metric,
                "Тип контрагента": "not_applicable",
                "Валюта": "EUR",
                "Сумма исходная": fact_value,
                "План, EUR": plan_value,
                "Факт, EUR": fact_value,
                "source_file": CONS_BUDGET_PATH.name,
                "source_row_id": f"{row['Месяц']}|{metric}",
            }
        )
    return pd.DataFrame(rows)


def add_inout_window(stage: pd.DataFrame, cons_budget: pd.DataFrame) -> pd.DataFrame:
    inout = (
        cons_budget[cons_budget["metric"].eq("IN-OUT")][["Месяц", "Факт, EUR"]]
        .rename(columns={"Факт, EUR": "IN-OUT, EUR"})
        .drop_duplicates("Месяц")
    )
    return stage.merge(inout, on="Месяц", how="left")


def prepare_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    text_cols = [col for col in df.columns if df[col].dtype == object or pd.api.types.is_string_dtype(df[col])]
    df[text_cols] = df[text_cols].replace({r"[\r\n]+": " "}, regex=True)
    for col in ["Ключ контрагента", "source_row_id", "Код статьи ДДС"]:
        if col in df.columns:
            df[col] = df[col].astype("string")
    return df


def with_article_and_counterparty(df: pd.DataFrame, article_ref: pd.DataFrame, source_layer: str) -> pd.DataFrame:
    diagnostic = df.merge(article_ref, on="Код статьи ДДС", how="left")
    diagnostic["source_layer"] = source_layer
    diagnostic["Тип"] = diagnostic["Тип статьи"].fillna("")
    for col in ["Статья 1", "Статья 2", "Статья"]:
        diagnostic[col] = diagnostic[col].fillna(diagnostic["Статья ДДС"])
    diagnostic["Тип периода"] = diagnostic["Тип периода"].replace({"future": "planning"})
    diagnostic = diagnostic.rename(columns={"Сумма (план)": "План, EUR", "Сумма (факт)": "Факт, EUR"})
    diagnostic["План, EUR"] = diagnostic["План, EUR"].fillna(0.0)
    diagnostic["Факт, EUR"] = diagnostic["Факт, EUR"].fillna(0.0)
    for col in ["Юр. лицо", "Контрагент", "Тип контрагента", "Валюта", "Сумма исходная"]:
        diagnostic[col] = diagnostic[col].fillna("")

    adjustment_mask = diagnostic["Источник данных"].eq("p-fact_adjustment")
    diagnostic.loc[adjustment_mask, "Юр. лицо"] = "not_applicable"
    diagnostic.loc[adjustment_mask, "Тип контрагента"] = "not_applicable"
    diagnostic.loc[adjustment_mask, "Контрагент"] = "p-fact"
    diagnostic.loc[adjustment_mask, "Валюта"] = "EUR"
    source_mask = diagnostic["Источник данных"].isin(["budget_rows", "dds"])
    diagnostic.loc[source_mask & diagnostic["Юр. лицо"].astype(str).str.strip().eq(""), "Юр. лицо"] = "unknown"
    diagnostic.loc[source_mask & diagnostic["Тип контрагента"].astype(str).str.strip().eq(""), "Тип контрагента"] = "unknown"

    counterparty = diagnostic["Контрагент"].map(split_counterparty)
    diagnostic["Контрагент"] = [item[0] for item in counterparty]
    diagnostic["Ключ контрагента"] = [item[1] for item in counterparty]
    diagnostic.loc[adjustment_mask, "Ключ контрагента"] = "p_fact"

    columns = [
        "source_layer",
        "Месяц",
        "Дата",
        "Тип периода",
        "Код статьи ДДС",
        "Тип",
        "Статья 1",
        "Статья 2",
        "Статья",
        "ЦФО",
        "Юр. лицо",
        "Контрагент",
        "Ключ контрагента",
        "Тип контрагента",
        "Валюта",
        "Сумма исходная",
        "План, EUR",
        "Факт, EUR",
        "is_player_refund",
        "included_in_reconciliation",
        "source_file",
        "source_row_id",
    ]
    return diagnostic[columns].reset_index(drop=True)


def build_p_fact_diagnostic(p_fact: pd.DataFrame) -> pd.DataFrame:
    diagnostic = p_fact.rename(columns={"План": "План, EUR", "Факт": "Факт, EUR"}).copy()
    diagnostic.insert(0, "source_layer", "p_fact")
    diagnostic["source_file"] = "p-fact_" + diagnostic["Месяц"].astype(str) + ".xlsx"
    diagnostic["source_row_id"] = (
        diagnostic["Месяц"].astype(str)
        + "|"
        + diagnostic["ЦФО"].astype(str)
        + "|"
        + diagnostic["Код статьи ДДС"].astype(str)
    )
    return diagnostic[
        [
            "source_layer",
            "Месяц",
            "ЦФО",
            "Код статьи ДДС",
            "План, EUR",
            "Факт, EUR",
            "source_file",
            "source_row_id",
        ]
    ].reset_index(drop=True)


def build_cons_budget_diagnostic(cons_budget: pd.DataFrame, p_fact_months: set[str]) -> pd.DataFrame:
    diagnostic = cons_budget.copy()
    diagnostic.loc[classify_period_series(diagnostic["Месяц"]).eq("planning"), "Факт, EUR"] = np.nan
    diagnostic.insert(0, "source_layer", "cons_budget")
    diagnostic["Дата"] = diagnostic["Месяц"].astype(str) + "-01"
    diagnostic["Статья"] = diagnostic["metric"]
    diagnostic["source_file"] = CONS_BUDGET_PATH.name
    diagnostic["source_row_id"] = diagnostic["Месяц"].astype(str) + "|" + diagnostic["metric"].astype(str)
    return diagnostic[
        [
            "source_layer",
            "Месяц",
            "Дата",
            "Статья",
            "План, EUR",
            "Факт, EUR",
            "source_file",
            "source_row_id",
        ]
    ].reset_index(drop=True)


def build_diagnostic_stages(
    p_fact: pd.DataFrame,
    budget_rows: pd.DataFrame,
    dds: pd.DataFrame,
    adjusted_union: pd.DataFrame,
    article_ref: pd.DataFrame,
    cons_budget: pd.DataFrame,
    p_fact_months: set[str],
) -> dict[str, pd.DataFrame]:
    adjustment_rows = adjusted_union[adjusted_union["Источник данных"].eq("p-fact_adjustment")].copy()
    return {
        "p_fact": build_p_fact_diagnostic(p_fact),
        "budget_rows": with_article_and_counterparty(budget_rows, article_ref, "budget_rows"),
        "dds": with_article_and_counterparty(dds, article_ref, "dds"),
        "p_fact_adjustments": with_article_and_counterparty(adjustment_rows, article_ref, "p_fact_adjustment"),
        "cons_budget": build_cons_budget_diagnostic(cons_budget, p_fact_months),
    }


def write_stage_csv(df: pd.DataFrame, path: Path) -> None:
    csv_kwargs = dict(
        index=False,
        encoding="utf-8-sig",
        sep=";",
        decimal=",",
        quoting=csv.QUOTE_MINIMAL,
        escapechar="\\",
        lineterminator="\n",
    )
    prepare_for_csv(df).to_csv(path, **csv_kwargs)


def build_full_stage(
    union_df: pd.DataFrame,
    article_ref: pd.DataFrame,
    cons_budget: pd.DataFrame,
    p_fact_months: set[str],
) -> pd.DataFrame:
    stage = union_df.merge(article_ref, on="Код статьи ДДС", how="left")
    stage["Тип"] = stage["Тип статьи"].fillna("")
    stage["Направление"] = stage["Направление"].where(stage["Направление"].isin(["inflow", "outflow"]), "unknown")
    for col in ["Статья 1", "Статья 2", "Статья"]:
        stage[col] = stage[col].fillna(stage["Статья ДДС"])
    stage = stage.rename(columns={"Сумма (план)": "План, EUR", "Сумма (факт)": "Факт, EUR"})
    stage["Дата"] = stage["Дата"].fillna(pd.to_datetime(stage["Месяц"] + "-01").dt.strftime("%Y-%m-%d"))
    stage["Тип периода"] = classify_period_series(stage["Месяц"])
    stage["Источник данных"] = stage["Источник данных"].replace({"p-fact_adjustment": "p_fact_adjustment"})
    stage["План, EUR"] = stage["План, EUR"].fillna(0.0)
    stage["Факт, EUR"] = stage["Факт, EUR"].fillna(0.0)
    for col in ["Юр. лицо", "Контрагент", "Тип контрагента", "Валюта", "Сумма исходная"]:
        stage[col] = stage[col].fillna("")
    adjustment_mask = stage["Источник данных"].eq("p_fact_adjustment")
    stage.loc[adjustment_mask, "Юр. лицо"] = "not_applicable"
    stage.loc[adjustment_mask, "Тип контрагента"] = "not_applicable"
    stage.loc[adjustment_mask, "Контрагент"] = "p-fact"
    stage.loc[adjustment_mask, "Валюта"] = "EUR"
    source_mask = stage["Источник данных"].isin(["budget_rows", "dds"])
    stage.loc[source_mask & stage["Юр. лицо"].astype(str).str.strip().eq(""), "Юр. лицо"] = "unknown"
    stage.loc[source_mask & stage["Тип контрагента"].astype(str).str.strip().eq(""), "Тип контрагента"] = "unknown"
    stage["included_in_reconciliation"] = stage["included_in_reconciliation"].fillna(1).astype(int)
    stage["is_player_refund"] = stage["is_player_refund"].fillna(0).astype(int)
    stage["source_file"] = stage["source_file"].fillna("").astype(str)
    stage["source_row_id"] = stage["source_row_id"].fillna("").astype(str)
    counterparty = stage["Контрагент"].map(split_counterparty)
    stage["Контрагент"] = [item[0] for item in counterparty]
    stage["Ключ контрагента"] = [item[1] for item in counterparty]
    stage.loc[adjustment_mask, "Ключ контрагента"] = "p_fact"
    stage = restore_fact_counterparty_keys_from_plan(stage)
    stage["_has_plan"] = np.where(stage["Тип операции"].eq("План") | (adjustment_mask & stage["План, EUR"].ne(0)), 1, 0)
    after_cutoff = classify_period_series(stage["Месяц"]).eq("planning")
    stage.loc[after_cutoff & stage["Тип операции"].isin(["Факт", "Корректировка p-fact"]), "Факт, EUR"] = 0.0
    stage["_has_fact"] = np.where(
        (stage["Тип операции"].eq("Факт") & stage["Факт, EUR"].ne(0)) | (adjustment_mask & stage["Факт, EUR"].ne(0)),
        1,
        0,
    )
    stage["_has_p_fact_adjustment"] = adjustment_mask.astype(int)
    stage["_has_player_refund"] = stage["is_player_refund"].astype(int)
    stage["_refund_discriminator"] = stage["is_player_refund"].astype(int)
    stage["_source_amount"] = to_number(stage["Сумма исходная"]).fillna(0.0)

    group_cols = [
        "Месяц",
        "Дата",
        "Тип периода",
        "Код статьи ДДС",
        "Тип",
        "Статья 1",
        "Статья 2",
        "Статья",
        "ЦФО",
        "Юр. лицо",
        "Контрагент",
        "Ключ контрагента",
        "Тип контрагента",
        "Валюта",
        "_refund_discriminator",
    ]
    aggregated = stage.groupby(group_cols, as_index=False, dropna=False).agg(
        **{
            "Сумма исходная": ("_source_amount", "sum"),
            "План, EUR": ("План, EUR", "sum"),
            "Факт, EUR": ("Факт, EUR", "sum"),
            "has_plan": ("_has_plan", "max"),
            "has_fact": ("_has_fact", "max"),
            "has_p_fact_adjustment": ("_has_p_fact_adjustment", "max"),
            "has_player_refund": ("_has_player_refund", "max"),
            "source_file": ("source_file", join_unique),
            "source_row_id": ("source_row_id", join_unique),
        }
    )
    aggregated["included_in_reconciliation"] = np.where(aggregated["has_player_refund"].eq(1), 0, 1)
    aggregated["source_mix"] = aggregated.apply(classify_source_mix, axis=1)
    aggregated = aggregated.drop(columns=["_refund_discriminator"])
    cons_budget = cons_budget.copy()
    cons_budget.loc[classify_period_series(cons_budget["Месяц"]).eq("planning"), "Факт, EUR"] = np.nan
    service_rows = build_cons_budget_rows(cons_budget, p_fact_months)
    aggregated = pd.concat([aggregated, service_rows], ignore_index=True)
    aggregated = add_inout_window(aggregated, cons_budget)
    return aggregated[FULL_STAGE_COLUMNS].sort_values(
        ["Месяц", "Дата", "source_mix", "Код статьи ДДС", "ЦФО", "Контрагент", "Ключ контрагента"],
        kind="mergesort",
    ).reset_index(drop=True)


def run_pipeline(write_outputs: bool = True) -> dict[str, object]:
    with tempfile.TemporaryDirectory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        raw_art = read_xlsx(DDS_ARTICLE_PATH, tmp_path)
        cons_budget = load_cons_budget(tmp_path)
        budget_raw = read_budget_raw(tmp_path)
        p_fact = build_p_fact(tmp_path)
        valid_triples_df = p_fact[["Месяц", "ЦФО", "Код статьи ДДС"]].drop_duplicates().reset_index(drop=True)
        valid_pairs_df = p_fact[["ЦФО", "Код статьи ДДС"]].drop_duplicates().reset_index(drop=True)
        p_fact_months = set(p_fact["Месяц"].unique())
        budget_rows = build_budget_rows(budget_raw, valid_triples_df, valid_pairs_df, p_fact_months)
        dds = build_dds(tmp_path, valid_triples_df)
        article_ref = build_article_reference(budget_raw, raw_art)

    union_df = pd.concat([budget_rows, dds], ignore_index=True)
    union_df = apply_p_fact_adjustments(p_fact, union_df)
    reconciliation = build_reconciliation(p_fact, union_df)
    failed_pairs = int((~(reconciliation["ok_plan"] & reconciliation["ok_fact"])).sum())
    total_pairs = int(len(reconciliation))
    max_abs_plan_diff = float(reconciliation["diff_plan"].abs().max()) if total_pairs else 0.0
    max_abs_fact_diff = float(reconciliation["diff_fact"].abs().max()) if total_pairs else 0.0
    full_stage = build_full_stage(union_df, article_ref, cons_budget, p_fact_months)
    diagnostic_stages = build_diagnostic_stages(
        p_fact,
        budget_rows,
        dds,
        union_df,
        article_ref,
        cons_budget,
        p_fact_months,
    )

    if failed_pairs:
        raise RuntimeError(f"p-fact reconciliation failed: reconciliation_failed_pairs={failed_pairs}")

    if write_outputs:
        STAGE_DIR.mkdir(parents=True, exist_ok=True)
        AUDIT_DIR.mkdir(parents=True, exist_ok=True)
        for old_output in [*OLD_USER_OUTPUTS, *OLD_DIAGNOSTIC_OUTPUTS]:
            old_output.unlink(missing_ok=True)
        write_stage_csv(full_stage, FULL_STAGE_OUTPUT)
        for name, path in DIAGNOSTIC_OUTPUTS.items():
            write_stage_csv(diagnostic_stages[name], path)

    return {
        "full_stage": full_stage,
        "reconciliation": reconciliation,
        "reconciliation_failed_pairs": failed_pairs,
        "total_reconciliation_pairs": total_pairs,
        "max_abs_plan_diff": max_abs_plan_diff,
        "max_abs_fact_diff": max_abs_fact_diff,
        "union": union_df,
        "diagnostic_stages": diagnostic_stages,
    }


def main() -> None:
    result = run_pipeline(write_outputs=True)
    print(f"full_stage: output={FULL_STAGE_OUTPUT} rows={len(result['full_stage'])}")
    print(f"reconciliation_failed_pairs={result['reconciliation_failed_pairs']}")
    print(f"total_reconciliation_pairs={result['total_reconciliation_pairs']}")
    print(f"max_abs_plan_diff={result['max_abs_plan_diff']}")
    print(f"max_abs_fact_diff={result['max_abs_fact_diff']}")


if __name__ == "__main__":
    main()
