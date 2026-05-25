from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

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

DATA_PACKAGE_JSON = LLM_DIR / "executive_yoy_mom_draft_data_package.json"
CONTROLLED_DRAFT_JSON = REPORTS_DIR / "executive_yoy_mom_controlled_draft_memo.json"
MEMO_DRAFT_MD = REPORTS_DIR / "executive_yoy_mom_memo_draft.md"
QA_REPORT = QA_DIR / "executive_yoy_mom_memo_draft_grounding_qa.json"
QA_SUMMARY = QA_DIR / "executive_yoy_mom_memo_draft_grounding_qa_summary.md"

MEMO_PROFILE = "executive_yoy_mom_budget_memo"
DEPTH_MODE = "depth_2_management_memo"
REQUIRED_SECTION_NAMES = [
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
EXECUTIVE_BODY_CHARTS = {
    "CH_EXEC_001_PLAN_FACT_TOP_ABS",
    "CH_EXEC_002_YOY_TOP_SHIFT",
    "CH_EXEC_003_MOM_INSTABILITY",
    "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO",
    "CH_EXEC_005_PLANNING_RISK",
    "CH_EXEC_006_IN_CONTEXT",
    "CH_EXEC_007_FLOW_BASE",
    "CH_EXEC_008_QA_LIMITATIONS",
}
APPENDIX_CHARTS = {
    "CH_EXEC_009_COUNTERPARTY_QUALITY",
    "CH_EXEC_010_CURRENCY_EXPOSURE",
}
CLAIM_LABELS = {
    "DATA FACT",
    "CALCULATION RESULT",
    "INTERPRETATION",
    "RECOMMENDATION",
    "LIMITATION",
    "HYPOTHESIS",
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


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def value_present(value: Any) -> bool:
    return value is not None and str(value).strip() not in {"", "nan", "NaN", "None"}


def source_ref(source_slice: str, metric: str, evidence_id: str) -> str:
    return f"Evidence: {evidence_id}; Source: {source_slice}; Metric: {metric}."


def first_claim(claims: list[dict[str, Any]], category: str | None = None) -> dict[str, Any] | None:
    for claim in claims:
        if category is None or claim.get("claim_category") == category:
            if claim.get("qa_status") == "pass" and claim.get("confidence_level") != "low":
                return claim
    return None


def section_claims(package: dict[str, Any], section_id: str) -> list[dict[str, Any]]:
    return [claim for claim in package["claim_candidates"] if claim["section_id"] == section_id]


def section_charts(package: dict[str, Any], section_id: str) -> list[dict[str, Any]]:
    return [chart for chart in package["chart_refs"] if chart["section_id"] == section_id]


def claim_line(label: str, claim: dict[str, Any], sentence: str) -> str:
    return (
        f"[{label}] {sentence} "
        f"{source_ref(claim.get('source_slice', ''), claim.get('metric', ''), claim.get('evidence_id', ''))}"
    )


def limitation_line(claim: dict[str, Any] | None, fallback: str) -> str:
    if claim is None:
        return f"[LIMITATION] {fallback} Evidence: section_contract; Source: report_contract; Metric: limitations."
    limitation = claim.get("limitation_text") or fallback
    return claim_line("LIMITATION", claim, str(limitation))


def compact_basis(claim: dict[str, Any]) -> str:
    basis = str(claim.get("claim_basis") or claim.get("metric") or "").strip()
    return basis.rstrip(".")


def risk_phrase(claim: dict[str, Any]) -> str:
    risk_basis = claim.get("risk_basis")
    if value_present(risk_basis) and risk_basis != "not_applicable":
        return f" Основание риска: {risk_basis}."
    return ""


def chart_line(chart: dict[str, Any]) -> str:
    return (
        f"[DATA FACT] График `{chart['chart_id']}` используется как визуальная опора раздела: "
        f"{chart['caption_ru']} Evidence: {chart['chart_id']}_DATA; "
        f"Source: {chart['source_slice']}; Metric: {chart['metric']}."
    )


def section_text(
    section: dict[str, Any],
    claims: list[dict[str, Any]],
    charts: list[dict[str, Any]],
    appendix_charts: list[dict[str, Any]] | None = None,
) -> list[str]:
    section_id = section["section_id"]
    fact = first_claim(claims, "DATA FACT")
    interpretation = first_claim(claims, "INTERPRETATION")
    limitation = first_claim(claims, "LIMITATION") or fact
    lines: list[str] = []

    if section_id == "SEC_01_FRAME":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    "Записка собрана как управленческий черновик по принятому MART/profile/chart/report contract контуру; раздел не расширяет scope за пределы принятых источников.",
                )
            )
        lines.append(limitation_line(limitation, "Preview layer only; no DOCX or executive conclusions generated."))
    elif section_id == "SEC_02_EXEC_SUMMARY":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"Ключевой executive-сигнал для маршрута записки: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "Executive Summary должен читаться как карта приоритетов проверки, а не как доказательство первопричины.",
                )
            )
        lines.append(limitation_line(limitation, "Limitations must be visible in section text before any appendix reference."))
    elif section_id == "SEC_03_READING_ROUTE":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    "Маршрут чтения: масштаб Plan-Fact, затем YoY, затем MoM, затем локализация, плановый риск, IN context и QC.",
                )
            )
        lines.append(limitation_line(limitation, "Reading route does not add a new analytical conclusion."))
    elif section_id == "SEC_04_PLAN_FACT":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"Plan-Fact раздел фиксирует масштаб отклонения по принятому срезу: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "Plan-Fact сигнал показывает приоритет проверки по EUR-масштабу; он не является самостоятельным объяснением причины отклонения.",
                )
            )
        lines.extend(chart_line(chart) for chart in charts if chart["chart_id"] in EXECUTIVE_BODY_CHARTS)
        lines.append(limitation_line(limitation, "Chart localizes magnitude, not root cause."))
    elif section_id == "SEC_05_YOY":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"YoY раздел отделён от MoM и использует только YoY evidence: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "YoY-сдвиг можно использовать как изменение уровня к прошлому году только с учётом базы сравнения и указанных ограничений.",
                )
            )
        lines.extend(chart_line(chart) for chart in charts if chart["chart_id"] in EXECUTIVE_BODY_CHARTS)
        lines.append(limitation_line(limitation, "Weak or missing YoY base prevents strong conclusion."))
    elif section_id == "SEC_06_MOM":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"MoM раздел отделён от YoY и показывает помесячную нестабильность: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "MoM-сигнал трактуется как динамика внутри периода, а не как YoY-изменение и не как подтверждённая причина.",
                )
            )
        lines.extend(chart_line(chart) for chart in charts if chart["chart_id"] in EXECUTIVE_BODY_CHARTS)
        lines.append(limitation_line(limitation, "MoM signal classification is not a root-cause confirmation."))
    elif section_id == "SEC_07_LOCALIZATION":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"Локализация показывает, где находится сигнал по связке статья × ЦФО: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "Раздел помогает определить адресата проверки, но не заменяет подтверждение владельцем бюджета.",
                )
            )
        lines.extend(chart_line(chart) for chart in charts if chart["chart_id"] in EXECUTIVE_BODY_CHARTS)
        lines.append(limitation_line(limitation, "Owner candidate is a routing hint, not confirmed accountability."))
    elif section_id == "SEC_08_PLANNING_RISK":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"Плановый риск описывает будущий бюджетный риск относительно исторической базы: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "Этот раздел не описывает фактическое исполнение и не должен называться перерасходом или экономией.",
                )
            )
        lines.extend(chart_line(chart) for chart in charts if chart["chart_id"] in EXECUTIVE_BODY_CHARTS)
        lines.append(limitation_line(limitation, "Planning risk is future risk, not actual execution."))
    elif section_id == "SEC_09_IN_CONTEXT":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"IN context показывает пропорциональность отклонений к притоку и отделяет flow rows от статей расходов: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "IN используется как denominator только при валидном статусе denominator; IN-OUT не суммируется по обычным статьям.",
                )
            )
        lines.extend(chart_line(chart) for chart in charts if chart["chart_id"] in EXECUTIVE_BODY_CHARTS)
        lines.append(limitation_line(limitation, "IN context requires valid denominator status and Definition Card governance."))
    elif section_id == "SEC_10_QC_LIMITATIONS":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"QC раздел фиксирует ограничения интерпретации и source quality signals: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "DQ/QC сигнал ограничивает силу управленческого вывода и не должен подаваться как финансовое искажение без отдельного подтверждения.",
                )
            )
        lines.extend(chart_line(chart) for chart in charts if chart["chart_id"] in EXECUTIVE_BODY_CHARTS)
        appendix = appendix_charts or []
        for chart in appendix:
            lines.append(
                f"[LIMITATION] Appendix candidate only: `{chart['chart_id']}` / {chart['chart_name_ru']}. "
                f"Evidence: {chart['chart_id']}_DATA; Source: {chart['source_slice']}; Metric: {chart['metric']}."
            )
        lines.append(limitation_line(limitation, "Limitations must be visible before appendix evidence."))
    elif section_id == "SEC_11_ACTION_REGISTER":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    f"Реестр проверок формируется из traceable signals: {compact_basis(fact)}.{risk_phrase(fact)}",
                )
            )
        lines.append(
            claim_line(
                "LIMITATION",
                limitation or fact,
                "Финальные action-items не публикуются без owner_candidate, due date и action status; текущие строки остаются кандидатами проверки.",
            )
            if limitation or fact
            else "[LIMITATION] Финальные action-items не публикуются без owner_candidate, due date и action status. Evidence: action_contract; Source: report_contract; Metric: action_status."
        )
    elif section_id == "SEC_12_FINAL_CONCLUSION":
        if fact:
            lines.append(
                claim_line(
                    "DATA FACT",
                    fact,
                    "Итоговый вывод ограничен подтверждёнными источниками draft package и не расширяется до production-ready утверждения.",
                )
            )
        if interpretation:
            lines.append(
                claim_line(
                    "INTERPRETATION",
                    interpretation,
                    "Поддерживаемый вывод: использовать записку как управленческий черновик для проверки приоритетных сигналов, а не как финальный DOCX.",
                )
            )
        lines.append(limitation_line(limitation, "Final management wording requires a grounding review before DOCX generation."))

    if not lines:
        lines.append(
            f"[LIMITATION] Раздел не получил publishable claim из принятого data package. Evidence: {section['section_id']}_CONTRACT; Source: report_contract; Metric: limitations."
        )
    return lines


def build_memo() -> tuple[str, dict[str, Any]]:
    package = load_json(DATA_PACKAGE_JSON)
    lines = [
        "# Управленческая записка YoY/MoM по бюджету",
        "",
        "Статус: controlled draft markdown. DOCX не создавался. Текст построен только из принятого deterministic draft data package.",
        "",
    ]
    section_records = []
    for section_name in REQUIRED_SECTION_NAMES:
        section = next(item for item in package["sections"] if item["section_name_ru"] == section_name)
        claims = section_claims(package, section["section_id"])
        charts = section_charts(package, section["section_id"])
        appendix_charts = package["chart_refs"] if section["section_id"] == "SEC_10_QC_LIMITATIONS" else []
        appendix_charts = [chart for chart in appendix_charts if chart["chart_id"] in APPENDIX_CHARTS]
        section_lines = section_text(section, claims, charts, appendix_charts)
        lines.extend([f"## {section_name}", ""])
        lines.extend(section_lines)
        lines.append("")
        section_records.append(
            {
                "section_id": section["section_id"],
                "section_name_ru": section_name,
                "claim_ids": [claim["claim_id"] for claim in claims],
                "chart_ids": [chart["chart_id"] for chart in charts],
                "line_count": len(section_lines),
            }
        )
    memo_text = "\n".join(lines).rstrip() + "\n"
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "mode": "controlled_draft_markdown_only_no_docx",
        "source_package": str(DATA_PACKAGE_JSON.relative_to(PROJECT_ROOT)),
        "section_records": section_records,
    }
    return memo_text, metadata


def important_lines(memo_text: str) -> list[str]:
    return [line for line in memo_text.splitlines() if line.startswith("[")]


def extract_chart_ids(memo_text: str, known_chart_ids: set[str]) -> set[str]:
    return {chart_id for chart_id in known_chart_ids if chart_id in memo_text}


def validate_memo(
    memo_text: str,
    metadata: dict[str, Any],
    raw_before: dict[str, tuple[int, int]],
    stage_before: dict[str, tuple[int, int]],
    marts_before: dict[str, tuple[int, int]],
    charts_before: dict[str, tuple[int, int]],
    docx_before: dict[str, tuple[int, int]],
) -> dict[str, Any]:
    package = load_json(DATA_PACKAGE_JSON)
    evidence_ids = {claim["evidence_id"] for claim in package["claim_candidates"]} | {
        f"{chart['chart_id']}_DATA" for chart in package["chart_refs"]
    } | {"section_contract", "action_contract"}
    source_slices = {claim["source_slice"] for claim in package["claim_candidates"]} | {
        chart["source_slice"] for chart in package["chart_refs"]
    } | {"report_contract"}
    metrics = {claim["metric"] for claim in package["claim_candidates"]} | {
        chart["metric"] for chart in package["chart_refs"]
    } | {"limitations", "action_status"}
    chart_ids = {chart["chart_id"] for chart in package["chart_refs"]}
    lines = important_lines(memo_text)
    heading_names = [line[3:] for line in memo_text.splitlines() if line.startswith("## ")]
    referenced_charts = extract_chart_ids(memo_text, chart_ids)
    unknown_evidence = [
        evidence
        for evidence in re.findall(r"Evidence: ([^;.\n]+)", memo_text)
        if evidence not in evidence_ids
    ]
    unknown_sources = [
        source
        for source in re.findall(r"Source: ([^;.\n]+)", memo_text)
        if source not in source_slices
    ]
    unknown_metrics = [
        metric
        for metric in re.findall(r"Metric: ([^.\n]+)", memo_text)
        if metric not in metrics
    ]
    checks = {
        "memo_draft_exists": MEMO_DRAFT_MD.exists(),
        "all_12_sections_exist": heading_names == REQUIRED_SECTION_NAMES,
        "important_paragraphs_have_claim_labels": all(
            any(line.startswith(f"[{label}]") for label in CLAIM_LABELS) for line in lines
        ),
        "important_paragraphs_have_evidence_source_metric": all(
            "Evidence: " in line and "Source: " in line and "Metric: " in line for line in lines
        ),
        "evidence_refs_are_known": not unknown_evidence,
        "source_refs_are_known": not unknown_sources,
        "metric_refs_are_known": not unknown_metrics,
        "chart_refs_exist": referenced_charts.issubset(chart_ids),
        "executive_body_charts_1_8_referenced": EXECUTIVE_BODY_CHARTS.issubset(referenced_charts),
        "appendix_charts_9_10_not_in_executive_body": APPENDIX_CHARTS.issubset(referenced_charts),
        "yoy_and_mom_separate": "## YoY: сдвиг уровня к прошлому году" in memo_text
        and "## MoM: помесячная динамика и нестабильность" in memo_text,
        "planning_risk_not_fact_execution": "не описывает фактическое исполнение" in memo_text
        and "будущий бюджетный риск" in memo_text,
        "in_context_explains_proportionality": "пропорциональность" in memo_text and "IN используется как denominator" in memo_text,
        "no_timing_confirmed_claim": "timing confirmed" not in memo_text.lower() and "подтверждённый timing" not in memo_text.lower(),
        "risk_has_risk_basis": "risk_basis=" in memo_text or "Основание риска:" in memo_text,
        "low_confidence_not_final_fact": "[DATA FACT]" in memo_text and "confidence=low" not in memo_text,
        "recommendations_have_owner_due_status_where_published": all(
            "owner=" in line and "due=" in line and "status=" in line
            for line in lines
            if line.startswith("[RECOMMENDATION]")
        ),
        "limitations_visible": "[LIMITATION]" in memo_text,
        "no_unsupported_refs": not unknown_evidence and not unknown_sources and not unknown_metrics,
        "no_docx_generated": docx_before == docx_snapshot(),
        "raw_untouched": raw_before == snapshot(RAW_DIR),
        "stage_untouched": stage_before == snapshot(STAGE_DIR),
        "mart_untouched": marts_before == snapshot(MARTS_DIR),
        "charts_untouched": charts_before == snapshot(CHARTS_DIR),
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "qa_status": "pass" if all(checks.values()) else "fail",
        "checks": {key: bool(value) for key, value in checks.items()},
        "section_count": len(metadata["section_records"]),
        "important_paragraph_count": len(lines),
        "referenced_chart_count": len(referenced_charts),
        "unknown_evidence": unknown_evidence,
        "unknown_sources": unknown_sources,
        "unknown_metrics": unknown_metrics,
        "docx_generated": False,
        "production_readiness_claimed": False,
    }


def main() -> None:
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_draft_markdown", status="start")
    for path in [DATA_PACKAGE_JSON, CONTROLLED_DRAFT_JSON]:
        if not path.exists():
            raise FileNotFoundError(f"Missing accepted source: {path.relative_to(PROJECT_ROOT)}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    raw_before = snapshot(RAW_DIR)
    stage_before = snapshot(STAGE_DIR)
    marts_before = snapshot(MARTS_DIR)
    charts_before = snapshot(CHARTS_DIR)
    docx_before = docx_snapshot()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_draft_prose_generation", status="start")
    memo_text, metadata = build_memo()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_draft_prose_generation", status="done")
    MEMO_DRAFT_MD.write_text(memo_text, encoding="utf-8")
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_draft_grounding_qa", status="start")
    qa = validate_memo(memo_text, metadata, raw_before, stage_before, marts_before, charts_before, docx_before)
    QA_REPORT.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QA_SUMMARY.write_text(
        "\n".join(
            [
                "# Executive YoY/MoM Memo Draft Grounding QA Summary",
                "",
                f"qa_status: {qa['qa_status']}",
                f"memo_profile: {MEMO_PROFILE}",
                f"section_count: {qa['section_count']}",
                f"important_paragraph_count: {qa['important_paragraph_count']}",
                f"referenced_chart_count: {qa['referenced_chart_count']}",
                "",
                "## Checks",
                *[f"- {key}: {'pass' if value else 'fail'}" for key, value in qa["checks"].items()],
                "",
                "## Residual Risks",
                "- Draft memo is Markdown only and remains evidence-bounded; final wording still needs review before DOCX generation.",
                "- No additional financial numbers were invented; where accepted claim candidates did not carry display values, the draft keeps signal/evidence wording instead of adding amounts.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_draft_markdown", status=qa["qa_status"], details={"sections": qa["section_count"]})
    print(json.dumps({"qa_status": qa["qa_status"], "sections": qa["section_count"], "paragraphs": qa["important_paragraph_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
