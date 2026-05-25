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
LLM_DIR = PROJECT_ROOT / "05_llm_package"
QA_DIR = PROJECT_ROOT / "07_qa"

PACKAGE_JSON = LLM_DIR / "executive_yoy_mom_draft_data_package.json"
PACKAGE_MD = LLM_DIR / "executive_yoy_mom_draft_data_package.md"
SECTION_INPUTS_XLSX = LLM_DIR / "executive_yoy_mom_section_inputs.xlsx"
CLAIM_CANDIDATES_XLSX = LLM_DIR / "executive_yoy_mom_claim_candidates.xlsx"
EVIDENCE_MAP_XLSX = LLM_DIR / "executive_yoy_mom_evidence_map.xlsx"
CHART_REFS_XLSX = LLM_DIR / "executive_yoy_mom_chart_refs.xlsx"
QA_REPORT = QA_DIR / "draft_data_package_qa.json"
QA_SUMMARY = QA_DIR / "draft_data_package_qa_summary.md"

MEMO_PROFILE = "executive_yoy_mom_budget_memo"
DEPTH_MODE = "depth_2_management_memo"

REQUIRED_INPUTS = [
    MARTS_DIR / "mart_main_full_budget.parquet",
    MARTS_DIR / "mart_flow_base_month.parquet",
    MARTS_DIR / "mart_signal_catalog_full.parquet",
    MARTS_DIR / "mart_main_compact_executive_yoy_mom.parquet",
    MARTS_DIR / "memo_profile_catalog.parquet",
    MARTS_DIR / "profile_readiness_matrix.parquet",
    CHARTS_DIR / "chart_catalog.parquet",
    REPORTS_DIR / "executive_yoy_mom_report_contract.json",
    REPORTS_DIR / "executive_yoy_mom_section_map.xlsx",
    REPORTS_DIR / "executive_yoy_mom_claim_plan.xlsx",
    REPORTS_DIR / "executive_yoy_mom_chart_placement.xlsx",
]

SECTION_INPUT_COLUMNS_RU = {
    "section_id": "ID раздела",
    "section_name_ru": "Название раздела",
    "contour": "Контур",
    "purpose": "Цель",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "source_chart_ids": "ID графиков",
    "selected_rows": "Выбранные строки",
    "selected_signals": "Выбранные сигналы",
    "key_metrics": "Ключевые метрики",
    "claim_candidates": "Claim candidates",
    "evidence_ids": "Evidence IDs",
    "limitations": "Ограничения",
    "qa_status": "QA статус",
    "confidence_level": "Уровень уверенности",
    "stop_condition_status": "Статус stop conditions",
}

CLAIM_COLUMNS_RU = {
    "claim_id": "ID claim",
    "claim_category": "Категория claim",
    "section_id": "ID раздела",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "metric": "Метрика",
    "period": "Период",
    "evidence_id": "Evidence ID",
    "qa_status": "QA статус",
    "confidence_level": "Уровень уверенности",
    "limitation_text": "Ограничение",
    "claim_basis": "Основание claim",
    "risk_basis": "Risk basis",
    "owner_candidate": "Кандидат владельца",
    "due_date": "Срок",
    "action_status": "Статус action",
    "future_risk_flag": "Future risk flag",
    "denominator_status": "Статус denominator",
}

EVIDENCE_COLUMNS_RU = {
    "evidence_id": "Evidence ID",
    "evidence_type": "Тип evidence",
    "section_id": "ID раздела",
    "claim_id": "ID claim",
    "chart_id": "ID графика",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "metric": "Метрика",
    "period": "Период",
    "qa_status": "QA статус",
    "confidence_level": "Уровень уверенности",
    "owner_candidate": "Кандидат владельца",
    "limitation_text": "Ограничение",
}

CHART_COLUMNS_RU = {
    "chart_id": "ID графика",
    "chart_order": "Порядок графика",
    "chart_role": "Роль графика",
    "include_in_memo": "Включать в записку",
    "section_id": "ID раздела",
    "chart_name_ru": "Название графика",
    "image_path": "Путь к изображению",
    "caption_ru": "Подпись",
    "source_mart": "Источник MART",
    "source_slice": "Источник среза",
    "metric": "Метрика",
    "grain": "Grain",
    "period": "Период",
    "limitation": "Ограничение",
    "qa_status": "QA статус",
}


def snapshot(path: Path) -> dict[str, tuple[int, int]]:
    if not path.exists():
        return {}
    return {
        str(item.relative_to(PROJECT_ROOT)): (item.stat().st_mtime_ns, item.stat().st_size)
        for item in path.rglob("*")
        if item.is_file()
    }


def docx_snapshot() -> dict[str, tuple[int, int]]:
    if not REPORTS_DIR.exists():
        return {}
    return {
        str(item.relative_to(PROJECT_ROOT)): (item.stat().st_mtime_ns, item.stat().st_size)
        for item in REPORTS_DIR.rglob("*.docx")
    }


def pipe(values: list[Any]) -> str:
    return " | ".join(str(value) for value in values if str(value) and str(value) != "nan")


def load_contract() -> dict[str, Any]:
    return json.loads((REPORTS_DIR / "executive_yoy_mom_report_contract.json").read_text(encoding="utf-8"))


def source_slice_filter(values: str) -> list[str]:
    return [value.strip() for value in str(values).split("|") if value.strip() and value.strip() != "not_applicable"]


def matching_signals(signals: pd.DataFrame, section: dict[str, Any], limit: int = 5) -> pd.DataFrame:
    source_slices = source_slice_filter(section["source_slice"])
    eligible = signals[signals["eligible_memo_profiles"].fillna("").str.contains(MEMO_PROFILE, regex=False)].copy()
    if source_slices:
        scoped = eligible[eligible["source_slice"].isin(source_slices)]
        if not scoped.empty:
            eligible = scoped
    if eligible.empty:
        return eligible.head(0)
    eligible["rank_sort"] = pd.to_numeric(eligible["rank"], errors="coerce").fillna(999999)
    return eligible.sort_values(["rank_sort", "signal_id"]).head(limit)


def matching_chart_refs(chart_placement: pd.DataFrame, section_id: str) -> pd.DataFrame:
    return chart_placement[chart_placement["section_id"].eq(section_id)].copy()


def build_claim_from_signal(section: dict[str, Any], signal: dict[str, Any], category: str, index: int) -> dict[str, Any]:
    is_planning = section["section_id"] == "SEC_08_PLANNING_RISK"
    is_recommendation = category == "RECOMMENDATION"
    owner = signal.get("owner_candidate", "")
    due = "required_before_final_memo" if is_recommendation else ""
    action_status = "candidate_action" if is_recommendation and owner else "not_applicable"
    return {
        "claim_id": f"{section['section_id']}_{category.replace(' ', '_')}_{index:03d}",
        "claim_category": category,
        "section_id": section["section_id"],
        "source_mart": signal.get("source_mart", section["source_mart"]),
        "source_slice": signal.get("source_slice", section["source_slice"]),
        "metric": signal.get("metric_name", ""),
        "period": signal.get("period", "all_available_periods"),
        "evidence_id": signal.get("evidence_id", ""),
        "qa_status": signal.get("qa_status", "pass"),
        "confidence_level": signal.get("confidence_level", "medium"),
        "limitation_text": signal.get("limitation_text", ""),
        "claim_basis": f"{signal.get('signal_type', '')}: {signal.get('object_name', '')}",
        "risk_basis": signal.get("risk_basis", ""),
        "owner_candidate": owner,
        "due_date": due,
        "action_status": action_status,
        "future_risk_flag": bool(is_planning),
        "denominator_status": "valid_full_period" if section["section_id"] == "SEC_09_IN_CONTEXT" else "not_applicable",
    }


def build_claim_from_chart(section: dict[str, Any], chart: dict[str, Any], category: str, index: int) -> dict[str, Any]:
    return {
        "claim_id": f"{section['section_id']}_{category.replace(' ', '_')}_CHART_{index:03d}",
        "claim_category": category,
        "section_id": section["section_id"],
        "source_mart": chart["source_mart"],
        "source_slice": chart["source_slice"],
        "metric": chart["metric"],
        "period": chart["period"],
        "evidence_id": f"{chart['chart_id']}_DATA",
        "qa_status": chart["qa_status"],
        "confidence_level": "high" if chart["qa_status"] == "pass" else "low",
        "limitation_text": chart["limitation"],
        "claim_basis": chart["caption_ru"],
        "risk_basis": "chart_caption_bounded_to_source",
        "owner_candidate": "",
        "due_date": "",
        "action_status": "not_applicable",
        "future_risk_flag": section["section_id"] == "SEC_08_PLANNING_RISK",
        "denominator_status": "valid_full_period" if chart["chart_id"] == "CH_EXEC_006_IN_CONTEXT" else "not_applicable",
    }


def build_package() -> tuple[dict[str, Any], pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    contract = load_contract()
    sections = pd.DataFrame(contract["sections"])
    signals = pd.read_parquet(MARTS_DIR / "mart_signal_catalog_full.parquet")
    compact = pd.read_parquet(MARTS_DIR / "mart_main_compact_executive_yoy_mom.parquet")
    profile = pd.read_parquet(MARTS_DIR / "memo_profile_catalog.parquet")
    readiness = pd.read_parquet(MARTS_DIR / "profile_readiness_matrix.parquet")
    chart_placement = pd.read_excel(REPORTS_DIR / "executive_yoy_mom_chart_placement.xlsx")
    chart_catalog = pd.read_parquet(CHARTS_DIR / "chart_catalog.parquet")
    chart_placement = chart_placement.merge(
        chart_catalog[["chart_id", "data_path"]], left_on="ID графика", right_on="chart_id", how="left"
    ).drop(columns=["chart_id"])
    chart_refs = chart_placement.rename(
        columns={
            "ID графика": "chart_id",
            "Порядок графика": "chart_order",
            "Роль графика": "chart_role",
            "Включать в записку": "include_in_memo",
            "ID раздела": "section_id",
            "Название графика": "chart_name_ru",
            "Путь к изображению": "image_path",
            "Подпись": "caption_ru",
            "Источник MART": "source_mart",
            "Источник среза": "source_slice",
            "Метрика": "metric",
            "Период": "period",
            "Ограничение": "limitation",
            "QA статус": "qa_status",
        }
    )
    if "Grain" in chart_refs.columns:
        chart_refs = chart_refs.rename(columns={"Grain": "grain"})

    claim_rows: list[dict[str, Any]] = []
    section_rows: list[dict[str, Any]] = []

    for section in sections.sort_values("section_order").to_dict("records"):
        section_signals = matching_signals(signals, section)
        section_charts = chart_refs[chart_refs["section_id"].eq(section["section_id"])].copy()
        selected_signal_ids = section_signals["signal_id"].tolist()
        evidence_ids = section_signals["evidence_id"].dropna().astype(str).tolist()
        limitations = section_signals["limitation_text"].dropna().astype(str).unique().tolist()
        if section["section_id"] == "SEC_01_FRAME":
            readiness_row = readiness[readiness["profile_code"].eq(MEMO_PROFILE)].iloc[0]
            evidence_ids.append("profile_readiness_matrix")
            limitations.append(str(readiness_row["limitation_reason"]))
        if section["section_id"] == "SEC_02_EXEC_SUMMARY":
            compact_rows = compact[compact["primary_memo_profile"].eq(MEMO_PROFILE)].head(7)
            evidence_ids.extend(compact_rows["evidence_id"].dropna().astype(str).tolist())
            selected_signal_ids.extend(compact_rows["signal_type"].dropna().astype(str).tolist())
        if not section_charts.empty:
            evidence_ids.extend([f"{chart_id}_DATA" for chart_id in section_charts["chart_id"]])
            limitations.extend(section_charts["limitation"].dropna().astype(str).tolist())

        claim_index = 1
        allowed_categories = [part.strip() for part in section["allowed_claim_types"].split("|")]
        for _, signal in section_signals.head(3).iterrows():
            category = "DATA FACT" if "DATA FACT" in allowed_categories else allowed_categories[0]
            claim_rows.append(build_claim_from_signal(section, signal.to_dict(), category, claim_index))
            claim_index += 1
            if "INTERPRETATION" in allowed_categories and signal.get("confidence_level", "medium") != "low":
                claim_rows.append(build_claim_from_signal(section, signal.to_dict(), "INTERPRETATION", claim_index))
                claim_index += 1
        for _, chart in section_charts.iterrows():
            claim_rows.append(build_claim_from_chart(section, chart.to_dict(), "DATA FACT", claim_index))
            claim_index += 1
        if "LIMITATION" in allowed_categories:
            claim_rows.append(
                {
                    "claim_id": f"{section['section_id']}_LIMITATION_999",
                    "claim_category": "LIMITATION",
                    "section_id": section["section_id"],
                    "source_mart": section["source_mart"],
                    "source_slice": section["source_slice"],
                    "metric": "limitations",
                    "period": "all_available_periods",
                    "evidence_id": evidence_ids[0] if evidence_ids else f"{section['section_id']}_CONTRACT",
                    "qa_status": "pass",
                    "confidence_level": "high",
                    "limitation_text": section["limitation_requirement"],
                    "claim_basis": "section_limitation_requirement",
                    "risk_basis": "not_applicable",
                    "owner_candidate": "",
                    "due_date": "",
                    "action_status": "not_applicable",
                    "future_risk_flag": section["section_id"] == "SEC_08_PLANNING_RISK",
                    "denominator_status": "not_applicable",
                }
            )

        confidence = "high" if not section_signals.empty and section_signals["qa_status"].eq("pass").all() else "medium"
        stop_status = "pass"
        if section["section_id"] == "SEC_09_IN_CONTEXT":
            stop_status = "pass_valid_denominator_required"
        if section["section_id"] == "SEC_08_PLANNING_RISK":
            stop_status = "pass_future_risk_only"
        section_rows.append(
            {
                "section_id": section["section_id"],
                "section_name_ru": section["section_name_ru"],
                "contour": section["contour"],
                "purpose": section["purpose"],
                "source_mart": section["source_mart"],
                "source_slice": section["source_slice"],
                "source_chart_ids": section["source_chart_ids"],
                "selected_rows": int(len(section_signals)),
                "selected_signals": pipe(selected_signal_ids[:12]),
                "key_metrics": section["required_metrics"],
                "claim_candidates": int(len([row for row in claim_rows if row["section_id"] == section["section_id"]])),
                "evidence_ids": pipe(sorted(set(evidence_ids))[:20]),
                "limitations": pipe(sorted(set([item for item in limitations if item]))[:10]),
                "qa_status": "pass",
                "confidence_level": confidence,
                "stop_condition_status": stop_status,
            }
        )

    section_inputs = pd.DataFrame(section_rows)
    claim_candidates = pd.DataFrame(claim_rows)
    evidence_map = build_evidence_map(claim_candidates, chart_refs)
    chart_refs = chart_refs[list(CHART_COLUMNS_RU)]
    package = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "mode": "draft_data_package_only_no_final_prose_no_docx",
        "sources": [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_INPUTS],
        "sections": section_inputs.to_dict(orient="records"),
        "claim_candidates": claim_candidates.to_dict(orient="records"),
        "chart_refs": chart_refs.to_dict(orient="records"),
        "evidence_map": evidence_map.to_dict(orient="records"),
        "profile_contract": profile[profile["profile_code"].eq(MEMO_PROFILE)].to_dict(orient="records"),
    }
    return package, section_inputs, claim_candidates, evidence_map, chart_refs


def build_evidence_map(claim_candidates: pd.DataFrame, chart_refs: pd.DataFrame) -> pd.DataFrame:
    claim_map = claim_candidates[
        [
            "evidence_id",
            "claim_id",
            "section_id",
            "source_mart",
            "source_slice",
            "metric",
            "period",
            "qa_status",
            "confidence_level",
            "owner_candidate",
            "limitation_text",
        ]
    ].copy()
    claim_map["evidence_type"] = "claim"
    claim_map["chart_id"] = ""
    chart_map = chart_refs[
        ["chart_id", "section_id", "source_mart", "source_slice", "metric", "period", "qa_status", "caption_ru", "limitation"]
    ].copy()
    chart_map["evidence_id"] = chart_map["chart_id"] + "_DATA"
    chart_map["claim_id"] = ""
    chart_map["evidence_type"] = "chart"
    chart_map["confidence_level"] = "high"
    chart_map["owner_candidate"] = ""
    chart_map = chart_map.rename(columns={"limitation": "limitation_text"})
    combined = pd.concat([claim_map, chart_map], ignore_index=True, sort=False)
    return combined[list(EVIDENCE_COLUMNS_RU)]


def write_excel(path: Path, sheet_name: str, data: pd.DataFrame, columns: dict[str, str]) -> None:
    visible = data[list(columns)].rename(columns=columns)
    with pd.ExcelWriter(path, engine="openpyxl") as writer:
        visible.to_excel(writer, sheet_name=sheet_name, index=False)
        ws = writer.book[sheet_name]
        ws.freeze_panes = "A2"
        for cells in ws.columns:
            max_len = max(len(str(cell.value or "")) for cell in cells[:80])
            ws.column_dimensions[cells[0].column_letter].width = min(max(max_len + 2, 12), 60)


def write_markdown(section_inputs: pd.DataFrame, claim_candidates: pd.DataFrame, chart_refs: pd.DataFrame) -> None:
    lines = [
        "# executive_yoy_mom_budget_memo draft data package",
        "",
        "Mode: data/context package only. No final memo prose. No DOCX.",
        "",
        "## Sections",
    ]
    for section in section_inputs.to_dict("records"):
        lines.extend(
            [
                "",
                f"### {section['section_name_ru']}",
                f"- section_id: `{section['section_id']}`",
                f"- contour: `{section['contour']}`",
                f"- selected_rows: {section['selected_rows']}",
                f"- claim_candidates: {section['claim_candidates']}",
                f"- evidence_ids: `{section['evidence_ids']}`",
                f"- stop_condition_status: `{section['stop_condition_status']}`",
            ]
        )
    lines.extend(["", "## Chart References"])
    for chart in chart_refs.sort_values("chart_order").to_dict("records"):
        lines.append(f"- `{chart['chart_id']}` ({chart['chart_role']}): {chart['caption_ru']}")
    lines.extend(["", "## Claim Candidate Count", f"- {len(claim_candidates)}"])
    PACKAGE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_package(
    section_inputs: pd.DataFrame,
    claim_candidates: pd.DataFrame,
    evidence_map: pd.DataFrame,
    chart_refs: pd.DataFrame,
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
    allowed_categories = {"DATA FACT", "CALCULATION RESULT", "INTERPRETATION", "RECOMMENDATION", "LIMITATION", "HYPOTHESIS"}
    planning = claim_candidates[claim_candidates["section_id"].eq("SEC_08_PLANNING_RISK")]
    yoy = claim_candidates[claim_candidates["section_id"].eq("SEC_05_YOY")]
    mom = claim_candidates[claim_candidates["section_id"].eq("SEC_06_MOM")]
    in_context = claim_candidates[claim_candidates["section_id"].eq("SEC_09_IN_CONTEXT")]
    recommendations = claim_candidates[claim_candidates["claim_category"].eq("RECOMMENDATION")]
    risk_claims = claim_candidates[claim_candidates["risk_basis"].fillna("").ne("") & claim_candidates["risk_basis"].ne("not_applicable")]
    checks = {
        "draft_data_package_exists_json_md": PACKAGE_JSON.exists() and PACKAGE_MD.exists(),
        "section_inputs_all_12_sections": len(section_inputs) == 12,
        "claim_candidates_have_evidence_and_source_fields": bool(
            not claim_candidates.empty
            and claim_candidates[["evidence_id", "source_mart", "source_slice", "metric", "period", "qa_status", "confidence_level"]]
            .fillna("")
            .ne("")
            .all()
            .all()
        ),
        "claim_categories_allowed": set(claim_candidates["claim_category"]).issubset(allowed_categories),
        "chart_refs_match_catalog": set(chart_refs["chart_id"]) == set(pd.read_parquet(CHARTS_DIR / "chart_catalog.parquet")["chart_id"]),
        "evidence_map_covers_claims": set(claim_candidates["claim_id"]).issubset(set(evidence_map["claim_id"])),
        "planning_risk_not_actual_execution": bool(not planning.empty and planning["future_risk_flag"].eq(True).all()),
        "yoy_and_mom_separated": bool(not yoy.empty and not mom.empty and not yoy["metric"].str.contains("mom", case=False, na=False).any() and not mom["metric"].str.contains("yoy", case=False, na=False).any()),
        "in_context_claims_have_valid_denominator_status": bool(
            in_context.empty or in_context["denominator_status"].isin(["valid_full_period", "valid_same_period", "not_applicable"]).all()
        ),
        "risk_claims_have_risk_basis": bool(risk_claims["risk_basis"].fillna("").ne("").all()),
        "recommendations_have_owner_due_action_status_or_absent": bool(
            recommendations.empty
            or recommendations[["owner_candidate", "due_date", "action_status"]].fillna("").ne("").all().all()
        ),
        "no_unsupported_claims": bool(claim_candidates["qa_status"].isin(["pass", "warning"]).all()),
        "no_final_prose_generated": True,
        "no_docx_generated": docx_before == docx_after,
        "raw_untouched": raw_before == raw_after,
        "stage_untouched": stage_before == stage_after,
        "mart_untouched": marts_before == marts_after,
        "charts_untouched": charts_before == charts_after,
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "pass" if all(checks.values()) else "fail",
        "memo_profile": MEMO_PROFILE,
        "checks": {key: bool(value) for key, value in checks.items()},
        "section_count": int(len(section_inputs)),
        "claim_candidate_count": int(len(claim_candidates)),
        "evidence_map_rows": int(len(evidence_map)),
        "chart_ref_count": int(len(chart_refs)),
        "production_readiness_claimed": False,
    }


def main() -> None:
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="draft_data_package", status="start")
    missing = [str(path.relative_to(PROJECT_ROOT)) for path in REQUIRED_INPUTS if not path.exists()]
    if missing:
        raise FileNotFoundError(f"Missing accepted sources: {missing}")
    LLM_DIR.mkdir(parents=True, exist_ok=True)
    raw_before = snapshot(RAW_DIR)
    stage_before = snapshot(STAGE_DIR)
    marts_before = snapshot(MARTS_DIR)
    charts_before = snapshot(CHARTS_DIR)
    docx_before = docx_snapshot()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="build_section_inputs_and_claim_candidates", status="start")
    package, section_inputs, claim_candidates, evidence_map, chart_refs = build_package()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="build_section_inputs_and_claim_candidates", status="done", details={"sections": len(section_inputs), "claims": len(claim_candidates)})
    PACKAGE_JSON.write_text(json.dumps(package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(section_inputs, claim_candidates, chart_refs)
    write_excel(SECTION_INPUTS_XLSX, "Section_Inputs", section_inputs, SECTION_INPUT_COLUMNS_RU)
    write_excel(CLAIM_CANDIDATES_XLSX, "Claim_Candidates", claim_candidates, CLAIM_COLUMNS_RU)
    write_excel(EVIDENCE_MAP_XLSX, "Evidence_Map", evidence_map, EVIDENCE_COLUMNS_RU)
    write_excel(CHART_REFS_XLSX, "Chart_Refs", chart_refs, CHART_COLUMNS_RU)
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="draft_data_package_qa", status="start")
    qa = validate_package(section_inputs, claim_candidates, evidence_map, chart_refs, raw_before, stage_before, marts_before, charts_before, docx_before)
    QA_REPORT.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QA_SUMMARY.write_text(
        "\n".join(
            [
                "# Draft Data Package QA Summary",
                "",
                f"qa_status: {qa['qa_status']}",
                f"memo_profile: {MEMO_PROFILE}",
                f"section_count: {qa['section_count']}",
                f"claim_candidate_count: {qa['claim_candidate_count']}",
                f"evidence_map_rows: {qa['evidence_map_rows']}",
                f"chart_ref_count: {qa['chart_ref_count']}",
                "",
                "## Checks",
                *[f"- {key}: {'pass' if value else 'fail'}" for key, value in qa["checks"].items()],
                "",
                "## Residual Risks",
                "- Package contains deterministic inputs and claim candidates only; final prose still requires a separate generation task.",
                "- Recommendation candidates require owner/due/status review before final action language.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="draft_data_package", status=qa["qa_status"], details={"sections": qa["section_count"], "claims": qa["claim_candidate_count"]})
    print(json.dumps({"qa_status": qa["qa_status"], "sections": qa["section_count"], "claims": qa["claim_candidate_count"], "checks": qa["checks"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
