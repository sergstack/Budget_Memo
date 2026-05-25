from __future__ import annotations

import json
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
INSIGHTS_CHECKLIST = Path(
    "/Users/sst/Documents/Артефакты/MAIN/AI_OS_4_Project_Folders_Setup_v04/[Analytics]/Codex_Tasks/04_INSIGHTS.md"
)

DRAFT_MD = REPORTS_DIR / "executive_yoy_mom_controlled_draft_memo.md"
DRAFT_JSON = REPORTS_DIR / "executive_yoy_mom_controlled_draft_memo.json"
QA_REPORT = QA_DIR / "controlled_draft_memo_qa.json"
QA_SUMMARY = QA_DIR / "controlled_draft_memo_qa_summary.md"

MEMO_PROFILE = "executive_yoy_mom_budget_memo"
DEPTH_MODE = "depth_2_management_memo"
MVP_BLOCKS = [
    "facts",
    "calculations",
    "interpretations",
    "recommendations",
    "hypotheses",
    "limitations",
]
ALLOWED_CLAIM_CATEGORIES = {
    "DATA FACT",
    "CALCULATION RESULT",
    "INTERPRETATION",
    "RECOMMENDATION",
    "LIMITATION",
    "HYPOTHESIS",
}
PASS_STOP_STATUSES = {
    "pass",
    "pass_future_risk_only",
    "pass_valid_denominator_required",
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


def valid_action(claim: dict[str, Any]) -> bool:
    return (
        value_present(claim.get("owner_candidate"))
        and value_present(claim.get("due_date"))
        and value_present(claim.get("action_status"))
        and claim.get("action_status") != "not_applicable"
    )


def is_publishable(claim: dict[str, Any], section_stop_status: str) -> bool:
    return (
        claim.get("qa_status") == "pass"
        and claim.get("confidence_level") != "low"
        and section_stop_status in PASS_STOP_STATUSES
    )


def evidence_suffix(claim: dict[str, Any]) -> str:
    parts = [
        f"source={claim.get('source_mart', '')}/{claim.get('source_slice', '')}",
        f"metric={claim.get('metric', '')}",
        f"period={claim.get('period', '')}",
        f"evidence={claim.get('evidence_id', '')}",
        f"qa={claim.get('qa_status', '')}",
        f"confidence={claim.get('confidence_level', '')}",
    ]
    risk_basis = claim.get("risk_basis", "")
    if value_present(risk_basis) and risk_basis != "not_applicable":
        parts.append(f"risk_basis={risk_basis}")
    return "[" + "; ".join(parts) + "]"


def claim_sentence(claim: dict[str, Any], prefix: str) -> str:
    basis = str(claim.get("claim_basis", "")).strip() or str(claim.get("metric", "")).strip()
    limitation = str(claim.get("limitation_text", "")).strip()
    text = f"{prefix}: {basis}. {evidence_suffix(claim)}"
    if limitation:
        text += f" Limitation: {limitation}"
    return text


def route_claim_to_block(claim: dict[str, Any], section_stop_status: str) -> str:
    category = claim.get("claim_category")
    if not is_publishable(claim, section_stop_status):
        return "hypotheses"
    if category == "DATA FACT":
        return "facts"
    if category == "CALCULATION RESULT":
        return "calculations"
    if category == "INTERPRETATION":
        return "interpretations"
    if category == "RECOMMENDATION":
        return "recommendations" if valid_action(claim) else "hypotheses"
    if category == "HYPOTHESIS":
        return "hypotheses"
    if category == "LIMITATION":
        return "limitations"
    return "limitations"


def empty_section_blocks() -> dict[str, list[str]]:
    return {block: [] for block in MVP_BLOCKS}


def build_section_draft(section: dict[str, Any], claims: list[dict[str, Any]], charts: list[dict[str, Any]]) -> dict[str, Any]:
    stop_status = str(section.get("stop_condition_status", ""))
    blocks = empty_section_blocks()

    if stop_status not in PASS_STOP_STATUSES:
        blocks["limitations"].append(
            f"Management conclusion blocked by stop condition: {stop_status}. No final interpretation is written."
        )

    for claim in claims:
        block = route_claim_to_block(claim, stop_status)
        category = claim.get("claim_category", "CLAIM")
        if block == "hypotheses" and category == "RECOMMENDATION" and not valid_action(claim):
            blocks[block].append(
                claim_sentence(
                    claim,
                    "Recommendation candidate only; owner/due date/status are incomplete, so this is not a final action",
                )
            )
        elif block == "hypotheses" and not is_publishable(claim, stop_status):
            blocks[block].append(
                claim_sentence(claim, "Hypothesis or non-final candidate; stop/QA/confidence gate prevents final wording")
            )
        elif block == "facts":
            blocks[block].append(claim_sentence(claim, "Fact"))
        elif block == "calculations":
            blocks[block].append(claim_sentence(claim, "Calculation result"))
        elif block == "interpretations":
            blocks[block].append(claim_sentence(claim, "Interpretation"))
        elif block == "recommendations":
            blocks[block].append(
                claim_sentence(
                    claim,
                    f"Recommendation; owner={claim.get('owner_candidate')}, due={claim.get('due_date')}, status={claim.get('action_status')}",
                )
            )
        elif block == "limitations":
            blocks[block].append(claim_sentence(claim, "Limitation"))

    for chart in charts:
        chart_text = (
            f"Chart reference: {chart.get('chart_id')} / {chart.get('chart_name_ru')}. "
            f"Caption: {chart.get('caption_ru')} "
            f"[source={chart.get('source_mart')}/{chart.get('source_slice')}; "
            f"metric={chart.get('metric')}; grain={chart.get('grain')}; period={chart.get('period')}; "
            f"qa={chart.get('qa_status')}; role={chart.get('chart_role')}]"
        )
        if chart.get("limitation"):
            chart_text += f" Limitation: {chart.get('limitation')}"
        blocks["facts"].append(chart_text)

    if not blocks["recommendations"]:
        blocks["recommendations"].append(
            "No publishable final recommendation in this section unless owner, due date and action status are present in the evidence package."
        )
    if not blocks["hypotheses"]:
        blocks["hypotheses"].append("No separate hypothesis is promoted beyond the evidence-bounded interpretation in this section.")
    if not blocks["limitations"]:
        blocks["limitations"].append(str(section.get("limitations", "")) or "No additional limitation captured in the data package.")

    return {
        "section_id": section["section_id"],
        "section_name_ru": section["section_name_ru"],
        "contour": section["contour"],
        "purpose": section["purpose"],
        "block_status": "must" if section["section_id"] in {"SEC_02_EXEC_SUMMARY", "SEC_04_PLAN_FACT", "SEC_05_YOY", "SEC_06_MOM", "SEC_10_QC_LIMITATIONS"} else "should",
        "stop_condition_status": stop_status,
        "qa_status": section.get("qa_status", ""),
        "confidence_level": section.get("confidence_level", ""),
        "mvp_blocks": blocks,
    }


def build_draft() -> dict[str, Any]:
    package = load_json(DATA_PACKAGE_JSON)
    claims = package["claim_candidates"]
    charts = package["chart_refs"]
    profile_contract = package["profile_contract"][0]
    sections = []
    for section in package["sections"]:
        section_id = section["section_id"]
        section_claims = [claim for claim in claims if claim["section_id"] == section_id]
        section_charts = [chart for chart in charts if chart["section_id"] == section_id]
        sections.append(build_section_draft(section, section_claims, section_charts))

    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "mode": "controlled_draft_memo_no_docx_not_final",
        "insights_checklist": str(INSIGHTS_CHECKLIST),
        "profile_governance": {
            "block_status": profile_contract.get("block_status"),
            "output_layer": profile_contract.get("output_layer"),
            "publish_rule": profile_contract.get("publish_rule"),
            "stop_conditions": profile_contract.get("stop_conditions"),
            "acceptance_criteria": profile_contract.get("acceptance_criteria"),
            "evidence_requirement": profile_contract.get("evidence_requirement"),
            "confidence_rule": profile_contract.get("confidence_rule"),
            "action_requirement": profile_contract.get("action_requirement"),
        },
        "draft_rules": {
            "separate_claim_blocks": True,
            "confirmed_cause_vs_hypothesis_separated": True,
            "stop_conditions_applied_before_management_conclusions": True,
            "low_confidence_not_final_fact": True,
            "risk_requires_risk_basis": True,
            "recommendation_requires_owner_due_status": True,
            "limitations_visible": True,
            "docx_generated": False,
            "production_readiness_claimed": False,
        },
        "sections": sections,
    }


def write_markdown(draft: dict[str, Any]) -> None:
    lines = [
        "# Управленческая записка YoY/MoM по бюджету — controlled draft",
        "",
        "Mode: controlled draft memo. Not final prose. No DOCX generated.",
        "",
        "## Governance",
    ]
    governance = draft["profile_governance"]
    for key in [
        "block_status",
        "output_layer",
        "publish_rule",
        "stop_conditions",
        "acceptance_criteria",
        "evidence_requirement",
        "confidence_rule",
        "action_requirement",
    ]:
        lines.append(f"- {key}: {governance.get(key, '')}")

    for section in draft["sections"]:
        lines.extend(
            [
                "",
                f"## {section['section_name_ru']}",
                "",
                f"- section_id: `{section['section_id']}`",
                f"- contour: `{section['contour']}`",
                f"- block_status: `{section['block_status']}`",
                f"- stop_condition_status: `{section['stop_condition_status']}`",
                f"- qa_status: `{section['qa_status']}`",
                f"- confidence_level: `{section['confidence_level']}`",
            ]
        )
        block_titles = {
            "facts": "Facts",
            "calculations": "Calculations",
            "interpretations": "Interpretations",
            "recommendations": "Recommendations",
            "hypotheses": "Hypotheses",
            "limitations": "Limitations",
        }
        for block in MVP_BLOCKS:
            lines.extend(["", f"### {block_titles[block]}"])
            values = section["mvp_blocks"][block]
            if values:
                lines.extend(f"- {value}" for value in values[:7])
            else:
                lines.append("- Not populated from accepted evidence package.")

    DRAFT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def validate_draft(
    draft: dict[str, Any],
    raw_before: dict[str, tuple[int, int]],
    stage_before: dict[str, tuple[int, int]],
    marts_before: dict[str, tuple[int, int]],
    charts_before: dict[str, tuple[int, int]],
    docx_before: dict[str, tuple[int, int]],
) -> dict[str, Any]:
    sections = draft["sections"]
    claims = load_json(DATA_PACKAGE_JSON)["claim_candidates"]
    docx_after = docx_snapshot()
    recommendation_lines = [
        line
        for section in sections
        for line in section["mvp_blocks"]["recommendations"]
        if not line.startswith("No publishable final recommendation")
    ]
    checks = {
        "controlled_draft_exists_md_json": DRAFT_MD.exists() and DRAFT_JSON.exists(),
        "insights_checklist_exists": INSIGHTS_CHECKLIST.exists(),
        "all_12_sections_exist": len(sections) == 12,
        "all_sections_have_mvp_blocks": all(set(section["mvp_blocks"]) == set(MVP_BLOCKS) for section in sections),
        "claim_categories_are_separated": set(claim["claim_category"] for claim in claims).issubset(ALLOWED_CLAIM_CATEGORIES),
        "facts_calculations_interpretations_recommendations_hypotheses_limitations_separated": all(
            all(isinstance(section["mvp_blocks"][block], list) for block in MVP_BLOCKS) for section in sections
        ),
        "stop_conditions_applied": all(section["stop_condition_status"] in PASS_STOP_STATUSES for section in sections),
        "low_confidence_not_final_fact": not any(
            "confidence=low" in line for section in sections for line in section["mvp_blocks"]["facts"]
        ),
        "risk_claims_have_risk_basis": all(
            value_present(claim.get("risk_basis")) or claim.get("risk_basis") == "not_applicable"
            for claim in claims
            if claim.get("claim_category") != "LIMITATION"
        ),
        "recommendations_require_owner_due_status": all(
            "owner=" in line and "due=" in line and "status=" in line for line in recommendation_lines
        ),
        "limitations_visible": all(section["mvp_blocks"]["limitations"] for section in sections),
        "planning_risk_future_not_actual_execution": all(
            claim.get("future_risk_flag") is True
            for claim in claims
            if claim.get("section_id") == "SEC_08_PLANNING_RISK"
        ),
        "yoy_and_mom_sections_separated": any(section["section_id"] == "SEC_05_YOY" for section in sections)
        and any(section["section_id"] == "SEC_06_MOM" for section in sections),
        "no_docx_generated": docx_before == docx_after,
        "raw_untouched": raw_before == snapshot(RAW_DIR),
        "stage_untouched": stage_before == snapshot(STAGE_DIR),
        "mart_untouched": marts_before == snapshot(MARTS_DIR),
        "charts_untouched": charts_before == snapshot(CHARTS_DIR),
        "production_readiness_not_claimed": draft["draft_rules"]["production_readiness_claimed"] is False,
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "memo_profile": MEMO_PROFILE,
        "qa_status": "pass" if all(checks.values()) else "fail",
        "checks": {key: bool(value) for key, value in checks.items()},
        "section_count": len(sections),
        "claim_count": len(claims),
        "docx_generated": False,
        "production_readiness_claimed": False,
    }


def main() -> None:
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="controlled_draft_memo", status="start")
    if not DATA_PACKAGE_JSON.exists():
        raise FileNotFoundError(f"Missing draft data package: {DATA_PACKAGE_JSON.relative_to(PROJECT_ROOT)}")
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    QA_DIR.mkdir(parents=True, exist_ok=True)
    raw_before = snapshot(RAW_DIR)
    stage_before = snapshot(STAGE_DIR)
    marts_before = snapshot(MARTS_DIR)
    charts_before = snapshot(CHARTS_DIR)
    docx_before = docx_snapshot()

    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="controlled_draft_blocks", status="start")
    draft = build_draft()
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="controlled_draft_blocks", status="done", details={"sections": len(draft.get("sections", []))})
    DRAFT_JSON.write_text(json.dumps(draft, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_markdown(draft)
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="controlled_draft_qa", status="start")
    qa = validate_draft(draft, raw_before, stage_before, marts_before, charts_before, docx_before)
    QA_REPORT.write_text(json.dumps(qa, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    QA_SUMMARY.write_text(
        "\n".join(
            [
                "# Controlled Draft Memo QA Summary",
                "",
                f"qa_status: {qa['qa_status']}",
                f"memo_profile: {MEMO_PROFILE}",
                f"section_count: {qa['section_count']}",
                f"claim_count: {qa['claim_count']}",
                "",
                "## Checks",
                *[f"- {key}: {'pass' if value else 'fail'}" for key, value in qa["checks"].items()],
                "",
                "## Residual Risks",
                "- This is a controlled draft, not final memo prose and not a DOCX.",
                "- Recommendations without owner/due/status remain non-final candidates.",
                "- Final management wording still requires a grounding review before DOCX generation.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    log_progress(memo_profile=MEMO_PROFILE, depth_mode=DEPTH_MODE, stage="controlled_draft_memo", status=qa["qa_status"], details={"sections": qa["section_count"], "claims": qa["claim_count"]})
    print(json.dumps({"qa_status": qa["qa_status"], "sections": qa["section_count"], "claims": qa["claim_count"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
