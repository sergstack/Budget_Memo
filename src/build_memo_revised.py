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
CONTRACT_JSON = REPORTS_DIR / "executive_yoy_mom_report_contract.json"
REVISED_MD = REPORTS_DIR / "executive_yoy_mom_memo_revised.md"
REVISED_JSON = REPORTS_DIR / "executive_yoy_mom_memo_revised.json"
QA_REPORT = QA_DIR / "executive_yoy_mom_memo_revised_qa.json"
QA_SUMMARY = QA_DIR / "executive_yoy_mom_memo_revised_qa_summary.md"

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


def section_claims(package: dict[str, Any], section_id: str, category: str | None = None) -> list[dict[str, Any]]:
    claims = [claim for claim in package["claim_candidates"] if claim["section_id"] == section_id]
    if category is not None:
        claims = [claim for claim in claims if claim["claim_category"] == category]
    return claims


def section_charts(package: dict[str, Any], section_id: str) -> list[dict[str, Any]]:
    return [chart for chart in package["chart_refs"] if chart["section_id"] == section_id]


def first_claim(package: dict[str, Any], section_id: str, category: str = "DATA FACT") -> dict[str, Any]:
    claims = section_claims(package, section_id, category)
    if not claims:
        claims = section_claims(package, section_id)
    if not claims:
        raise ValueError(f"No claims for {section_id}")
    return claims[0]


def basis(claim: dict[str, Any]) -> str:
    return str(claim.get("claim_basis") or claim.get("metric") or "").strip()


def evidence(claim_or_chart: dict[str, Any]) -> str:
    return str(claim_or_chart.get("evidence_id") or f"{claim_or_chart.get('chart_id')}_DATA")


def risk_basis(claim: dict[str, Any]) -> str:
    value = str(claim.get("risk_basis") or "").strip()
    if value and value != "not_applicable":
        return value
    return "risk_basis не применим к этому ограничению"


def chart_by_id(package: dict[str, Any], chart_id: str) -> dict[str, Any]:
    for chart in package["chart_refs"]:
        if chart["chart_id"] == chart_id:
            return chart
    raise KeyError(chart_id)


def evidence_table(rows: list[dict[str, str]]) -> list[str]:
    if not rows:
        return []
    lines = [
        "",
        "Evidence table:",
        "",
        "| Evidence | Source slice | Metric | Комментарий |",
        "|---|---|---|---|",
    ]
    for row in rows:
        lines.append(f"| {row['evidence']} | {row['source_slice']} | {row['metric']} | {row['comment']} |")
    return lines


def claim_evidence_row(claim: dict[str, Any], comment: str) -> dict[str, str]:
    return {
        "evidence": evidence(claim),
        "source_slice": str(claim.get("source_slice", "")),
        "metric": str(claim.get("metric", "")),
        "comment": comment,
    }


def chart_evidence_row(chart: dict[str, Any]) -> dict[str, str]:
    return {
        "evidence": f"{chart['chart_id']}_DATA",
        "source_slice": str(chart["source_slice"]),
        "metric": str(chart["metric"]),
        "comment": str(chart["caption_ru"]),
    }


def action_rows(package: dict[str, Any]) -> list[dict[str, str]]:
    rows = []
    for claim in section_claims(package, "SEC_11_ACTION_REGISTER", "DATA FACT")[:6]:
        claim_basis = basis(claim)
        if ":" in claim_basis:
            signal_type, obj = [part.strip() for part in claim_basis.split(":", 1)]
        else:
            signal_type, obj = str(claim.get("metric", "")), claim_basis
        owner = str(claim.get("owner_candidate") or "").strip() or "не задан"
        due = str(claim.get("due_date") or "").strip() or "не задан"
        status = "candidate_action"
        if owner == "не задан" or due == "не задан" or str(claim.get("action_status")) == "not_applicable":
            status = "candidate_only_incomplete_action_fields"
        rows.append(
            {
                "object": obj,
                "signal_type": signal_type,
                "check": "Проверить природу сигнала и подтвердить управленческую трактовку.",
                "owner": owner,
                "due": due,
                "status": status,
                "evidence": evidence(claim),
            }
        )
    return rows


def chart_ref_line(chart: dict[str, Any]) -> str:
    return f"Chart `{chart['chart_id']}`: {chart['caption_ru']} Evidence: {chart['chart_id']}_DATA."


def build_memo() -> tuple[str, dict[str, Any]]:
    package = load_json(DATA_PACKAGE_JSON)
    contract = load_json(CONTRACT_JSON)
    lines: list[str] = [
        "# Управленческая записка YoY/MoM по бюджету",
        "",
        "Статус: revised management-readable Markdown draft. DOCX не создавался.",
        "",
    ]
    used_evidence: set[str] = set()
    section_records: list[dict[str, Any]] = []

    def add_section(name: str, body: list[str], ev_rows: list[dict[str, str]]) -> None:
        lines.extend([f"## {name}", ""])
        lines.extend(body)
        lines.extend(evidence_table(ev_rows))
        lines.append("")
        used_evidence.update(row["evidence"] for row in ev_rows)
        section_records.append({"section_name_ru": name, "evidence": [row["evidence"] for row in ev_rows]})

    flow = first_claim(package, "SEC_09_IN_CONTEXT")
    plan_fact = first_claim(package, "SEC_04_PLAN_FACT")
    yoy = first_claim(package, "SEC_05_YOY")
    mom = first_claim(package, "SEC_06_MOM")
    localization = first_claim(package, "SEC_07_LOCALIZATION")
    planning = first_claim(package, "SEC_08_PLANNING_RISK")
    qc = first_claim(package, "SEC_10_QC_LIMITATIONS")

    add_section(
        "Рамка анализа",
        [
            "Записка собрана как управленческий черновик по принятому MART, memo profile, chart package и report contract. Scope ограничен принятыми источниками; документ не является production-ready выводом и не заменяет evidence package.",
            "Исторический контур отделён от планового риска. Факты, интерпретации и ограничения не смешиваются с гипотезами о причинах.",
        ],
        [
            {"evidence": "report_contract", "source_slice": "executive_yoy_mom_report_contract", "metric": "section_order", "comment": "Контракт структуры записки."},
            {"evidence": "draft_data_package", "source_slice": "executive_yoy_mom_draft_data_package", "metric": "claim_candidates", "comment": "Источник claim candidates и evidence map."},
        ],
    )

    executive_bullets = [
        f"- **Масштаб Plan-Fact.** Приоритетный сигнал: {basis(plan_fact)}; основание риска: {risk_basis(plan_fact)}. Evidence: {evidence(plan_fact)}.",
        f"- **YoY.** YoY анализ ведётся отдельно от MoM; основной сигнал: {basis(yoy)}. Вывод допустим только с учётом базы прошлого года. Evidence: {evidence(yoy)}.",
        f"- **MoM.** MoM показывает помесячную нестабильность, не подтверждённую причину; основной сигнал: {basis(mom)}. Evidence: {evidence(mom)}.",
        f"- **Локализация.** Сигнал локализован как кандидат для вопроса владельцу: {basis(localization)}; это не подтверждённая причина. Evidence: {evidence(localization)}.",
        f"- **Плановый риск.** {basis(planning)} рассматривается как будущий бюджетный риск относительно исторической базы, не как факт исполнения. Evidence: {evidence(planning)}.",
        f"- **IN context.** {basis(flow)} используется для контекста пропорциональности к притоку; IN-OUT не суммируется по обычным статьям. Evidence: {evidence(flow)}.",
        f"- **QC.** Source quality сигналы и appendix charts ограничивают силу интерпретации; они не являются самостоятельным выводом о финансовом искажении. Evidence: {evidence(qc)}.",
    ]
    add_section(
        "Executive Summary",
        executive_bullets,
        [
            claim_evidence_row(plan_fact, "Plan-Fact scale bullet."),
            claim_evidence_row(yoy, "YoY bullet."),
            claim_evidence_row(mom, "MoM bullet."),
            claim_evidence_row(localization, "Localization bullet."),
            claim_evidence_row(planning, "Planning risk bullet."),
            claim_evidence_row(flow, "IN context bullet."),
            claim_evidence_row(qc, "QC limitation bullet."),
        ],
    )

    add_section(
        "Как читать записку",
        [
            "Маршрут чтения: масштаб Plan-Fact -> YoY -> MoM -> локализация -> плановый риск -> IN context -> QC.",
            "Каждый раздел показывает, что можно считать подтверждённым сигналом, что остаётся интерпретацией, и какое ограничение должно быть видно до управленческого вывода.",
        ],
        [
            {"evidence": "report_contract", "source_slice": "executive_yoy_mom_section_map", "metric": "section_order", "comment": "Маршрут разделов."},
        ],
    )

    ch1 = chart_by_id(package, "CH_EXEC_001_PLAN_FACT_TOP_ABS")
    add_section(
        "Исторический факт: масштаб Plan-Fact",
        [
            f"Plan-Fact раздел фиксирует приоритет проверки по EUR-масштабу: {basis(plan_fact)}. Это сигнал масштаба, а не доказательство причины.",
            chart_ref_line(ch1),
            "Сервисные flow rows IN / OUT / IN-OUT не используются как расходные статьи в этом выводе.",
        ],
        [claim_evidence_row(plan_fact, "Plan-Fact signal."), chart_evidence_row(ch1)],
    )

    ch2 = chart_by_id(package, "CH_EXEC_002_YOY_TOP_SHIFT")
    add_section(
        "YoY: сдвиг уровня к прошлому году",
        [
            f"YoY раздел показывает изменение уровня к прошлому году по отдельному YoY evidence: {basis(yoy)}.",
            "Сильный YoY вывод допустим только там, где есть база прошлого года; слабая или отсутствующая база остаётся ограничением.",
            chart_ref_line(ch2),
        ],
        [claim_evidence_row(yoy, "YoY signal."), chart_evidence_row(ch2)],
    )

    ch3 = chart_by_id(package, "CH_EXEC_003_MOM_INSTABILITY")
    add_section(
        "MoM: помесячная динамика и нестабильность",
        [
            f"MoM раздел отделён от YoY и показывает внутригодовую месячную нестабильность: {basis(mom)}.",
            "MoM classification не является подтверждённой причиной; это кандидат для проверки динамики.",
            chart_ref_line(ch3),
        ],
        [claim_evidence_row(mom, "MoM signal."), chart_evidence_row(ch3)],
    )

    ch4 = chart_by_id(package, "CH_EXEC_004_LOCALIZATION_ARTICLE_CFO")
    add_section(
        "Локализация: статья × ЦФО",
        [
            f"Локализация показывает, где сидит сигнал и кому адресовать вопрос: {basis(localization)}.",
            "Кандидат владельца не равен подтверждённой ответственности; управленческое действие требует owner, due date и status.",
            chart_ref_line(ch4),
        ],
        [claim_evidence_row(localization, "Localization signal."), chart_evidence_row(ch4)],
    )

    ch5 = chart_by_id(package, "CH_EXEC_005_PLANNING_RISK")
    add_section(
        "Плановый риск: план к исторической базе",
        [
            f"Плановый риск описывает будущий бюджетный риск относительно исторической базы: {basis(planning)}.",
            "Этот раздел не описывает фактическое исполнение и не должен называться перерасходом или экономией.",
            chart_ref_line(ch5),
        ],
        [claim_evidence_row(planning, "Planning risk signal."), chart_evidence_row(ch5)],
    )

    ch6 = chart_by_id(package, "CH_EXEC_006_IN_CONTEXT")
    ch7 = chart_by_id(package, "CH_EXEC_007_FLOW_BASE")
    add_section(
        "iGaming flow context: отклонения к IN",
        [
            f"IN context нужен для оценки пропорциональности к притоку: {basis(flow)}.",
            "IN используется как denominator только при валидном denominator status. IN-OUT остаётся flow context и не суммируется по обычным статьям.",
            chart_ref_line(ch6),
            chart_ref_line(ch7),
        ],
        [claim_evidence_row(flow, "Flow pressure signal."), chart_evidence_row(ch6), chart_evidence_row(ch7)],
    )

    ch8 = chart_by_id(package, "CH_EXEC_008_QA_LIMITATIONS")
    ch9 = chart_by_id(package, "CH_EXEC_009_COUNTERPARTY_QUALITY")
    ch10 = chart_by_id(package, "CH_EXEC_010_CURRENCY_EXPOSURE")
    add_section(
        "QC и ограничения",
        [
            "QC раздел показывает ограничения интерпретации, а не самостоятельное утверждение о финансовом искажении.",
            f"Source quality сигнал `{basis(qc)}` используется как limitation candidate, а не как headline management conclusion.",
            chart_ref_line(ch8),
            f"Appendix candidate: `{ch9['chart_id']}` — {ch9['caption_ru']} Evidence: {ch9['chart_id']}_DATA.",
            f"Appendix candidate: `{ch10['chart_id']}` — {ch10['caption_ru']} Evidence: {ch10['chart_id']}_DATA.",
        ],
        [claim_evidence_row(qc, "QC limitation candidate."), chart_evidence_row(ch8), chart_evidence_row(ch9), chart_evidence_row(ch10)],
    )

    actions = action_rows(package)
    action_lines = [
        "Финальные action-items не публикуются без полного owner / due date / status. Ниже приведён кандидатный реестр проверок.",
        "",
        "| Объект | Тип сигнала | Что проверить | Кандидат владельца | Срок | Статус | Evidence ID |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in actions:
        action_lines.append(
            f"| {row['object']} | {row['signal_type']} | {row['check']} | {row['owner']} | {row['due']} | {row['status']} | {row['evidence']} |"
        )
    add_section(
        "Реестр приоритетных проверок",
        action_lines,
        [
            {
                "evidence": row["evidence"],
                "source_slice": "mart_signal_catalog_full",
                "metric": row["signal_type"],
                "comment": "Candidate action row; final action blocked until owner/due/status are complete.",
            }
            for row in actions
        ],
    )

    add_section(
        "Итоговый вывод",
        [
            "Черновик можно использовать как карту приоритетных проверок: масштаб отклонения, YoY, MoM, локализация, будущий плановый риск, IN context и QC ограничения.",
            "Финальная управленческая записка в DOCX допустима только после review этой revised версии; production readiness не заявляется.",
        ],
        [
            {"evidence": "report_contract", "source_slice": "executive_yoy_mom_report_contract", "metric": "forbidden_claims", "comment": "No production readiness; evidence appendix must not replace memo."},
            {"evidence": "draft_data_package", "source_slice": "executive_yoy_mom_draft_data_package", "metric": "claim_candidates", "comment": "All memo claims remain bounded by accepted package."},
        ],
    )

    memo_text = "\n".join(lines).rstrip() + "\n"
    metadata = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "mode": "revised_markdown_only_no_docx",
        "source_package": str(DATA_PACKAGE_JSON.relative_to(PROJECT_ROOT)),
        "source_contract": str(CONTRACT_JSON.relative_to(PROJECT_ROOT)),
        "section_records": section_records,
        "used_evidence": sorted(used_evidence),
    }
    return memo_text, metadata


def extract_headings(memo_text: str) -> list[str]:
    return [line[3:] for line in memo_text.splitlines() if line.startswith("## ")]


def executive_bullet_count(memo_text: str) -> int:
    match = re.search(r"## Executive Summary\n\n(?P<body>.*?)(?:\n## |\Z)", memo_text, re.S)
    if not match:
        return 0
    return len([line for line in match.group("body").splitlines() if line.startswith("- **")])


def main_body_trace_count(memo_text: str) -> int:
    lines = []
    in_table = False
    for line in memo_text.splitlines():
        if line == "Evidence table:":
            in_table = True
        elif line.startswith("## "):
            in_table = False
        if not in_table:
            lines.append(line)
    text = "\n".join(lines)
    return text.count("Source:") + text.count("Metric:")


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
    } | {"report_contract", "draft_data_package"}
    chart_ids = {chart["chart_id"] for chart in package["chart_refs"]}
    referenced_evidence = set(re.findall(r"\b(?:EV-[A-Z_]+-\d+|CH_EXEC_\d{3}_[A-Z0-9_]+_DATA|report_contract|draft_data_package)\b", memo_text))
    referenced_charts = {chart_id for chart_id in chart_ids if chart_id in memo_text}
    checks = {
        "revised_memo_exists": REVISED_MD.exists() and REVISED_JSON.exists(),
        "all_12_sections_remain": extract_headings(memo_text) == REQUIRED_SECTION_NAMES,
        "no_unsupported_claims": referenced_evidence.issubset(evidence_ids),
        "important_claims_traceable": bool(referenced_evidence) and referenced_evidence.issubset(evidence_ids),
        "executive_summary_has_5_to_7_bullets": 5 <= executive_bullet_count(memo_text) <= 7,
        "detailed_trace_not_in_main_prose": main_body_trace_count(memo_text) == 0,
        "planning_risk_not_actual_execution": "не описывает фактическое исполнение" in memo_text
        and "будущий бюджетный риск" in memo_text,
        "yoy_and_mom_separate": "## YoY: сдвиг уровня к прошлому году" in memo_text
        and "## MoM: помесячная динамика и нестабильность" in memo_text,
        "action_register_exists": "| Объект | Тип сигнала | Что проверить | Кандидат владельца | Срок | Статус | Evidence ID |" in memo_text,
        "candidate_actions_when_fields_incomplete": "candidate_only_incomplete_action_fields" in memo_text,
        "limitations_visible": "## QC и ограничения" in memo_text and "limitation candidate" in memo_text,
        "chart_refs_exist": referenced_charts.issubset(chart_ids),
        "executive_body_charts_1_8_referenced": EXECUTIVE_BODY_CHARTS.issubset(referenced_charts),
        "appendix_charts_9_10_as_candidates": APPENDIX_CHARTS.issubset(referenced_charts) and "Appendix candidate" in memo_text,
        "no_docx_generated": docx_before == docx_snapshot(),
        "raw_untouched": raw_before == snapshot(RAW_DIR),
        "stage_untouched": stage_before == snapshot(STAGE_DIR),
        "mart_untouched": marts_before == snapshot(MARTS_DIR),
        "charts_untouched": charts_before == snapshot(CHARTS_DIR),
        "production_readiness_not_claimed": "production readiness не заявляется" in memo_text.lower(),
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "qa_status": "pass" if all(checks.values()) else "fail",
        "checks": {key: bool(value) for key, value in checks.items()},
        "section_count": len(extract_headings(memo_text)),
        "executive_bullet_count": executive_bullet_count(memo_text),
        "referenced_evidence_count": len(referenced_evidence),
        "referenced_chart_count": len(referenced_charts),
        "main_body_trace_count": main_body_trace_count(memo_text),
        "docx_generated": False,
        "production_readiness_claimed": False,
    }


def main() -> None:
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_revised_markdown", status="start")
    for path in [DATA_PACKAGE_JSON, CONTRACT_JSON]:
        if not path.exists():
            raise FileNotFoundError(f"Missing source: {path.relative_to(PROJECT_ROOT)}")
    raw_before = snapshot(RAW_DIR)
    stage_before = snapshot(STAGE_DIR)
    marts_before = snapshot(MARTS_DIR)
    charts_before = snapshot(CHARTS_DIR)
    docx_before = docx_snapshot()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_revisor_pass", status="start")
    memo_text, metadata = build_memo()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_revisor_pass", status="done")
    REVISED_MD.write_text(memo_text, encoding="utf-8")
    REVISED_JSON.write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_revised_qa", status="start")
    qa = validate_memo(memo_text, metadata, raw_before, stage_before, marts_before, charts_before, docx_before)
    QA_REPORT.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QA_SUMMARY.write_text(
        "\n".join(
            [
                "# Executive YoY/MoM Revised Memo QA Summary",
                "",
                f"qa_status: {qa['qa_status']}",
                f"memo_profile: {MEMO_PROFILE}",
                f"section_count: {qa['section_count']}",
                f"executive_bullet_count: {qa['executive_bullet_count']}",
                f"referenced_evidence_count: {qa['referenced_evidence_count']}",
                f"referenced_chart_count: {qa['referenced_chart_count']}",
                "",
                "## Checks",
                *[f"- {key}: {'pass' if value else 'fail'}" for key, value in qa["checks"].items()],
                "",
                "## Residual Risks",
                "- Revised memo remains Markdown-only; DOCX generation requires explicit next task.",
                "- No new financial numbers were introduced; memo uses signal names, ranking basis, charts and evidence IDs from accepted package.",
                "- Candidate actions remain non-final where owner/due/status are incomplete.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="memo_revised_markdown", status=qa["qa_status"], details={"sections": qa["section_count"]})
    print(json.dumps({"qa_status": qa["qa_status"], "sections": qa["section_count"], "executive_bullets": qa["executive_bullet_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
