from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib import error, request

import pandas as pd

try:
    from src.ollama_routing import OLLAMA_FAST_FALLBACK_MODEL, OLLAMA_MODELS, OLLAMA_ROUTING_NOTE, OLLAMA_URL, model_for_role
    from src.progress import log_progress
except ImportError:  # pragma: no cover
    from ollama_routing import OLLAMA_FAST_FALLBACK_MODEL, OLLAMA_MODELS, OLLAMA_ROUTING_NOTE, OLLAMA_URL, model_for_role
    from progress import log_progress


PROJECT_ROOT = Path(__file__).resolve().parents[1]
LLM_DIR = PROJECT_ROOT / "05_llm_package"
REPORTS_DIR = PROJECT_ROOT / "06_reports"
QA_DIR = PROJECT_ROOT / "07_qa"
CHARTS_DIR = PROJECT_ROOT / "04_charts"
MARTS_DIR = PROJECT_ROOT / "03_marts"
RAW_DIR = PROJECT_ROOT / "01_raw"
STAGE_DIR = PROJECT_ROOT / "02_stage"

DRAFT_PACKAGE = LLM_DIR / "executive_yoy_mom_draft_data_package.json"
CLAIM_CANDIDATES_XLSX = LLM_DIR / "executive_yoy_mom_claim_candidates.xlsx"
EVIDENCE_MAP_XLSX = LLM_DIR / "executive_yoy_mom_evidence_map.xlsx"
CHART_CATALOG = CHARTS_DIR / "chart_catalog.parquet"
REPORT_CONTRACT = REPORTS_DIR / "01_executive_yoy_mom_budget_memo" / "source_refs" / "memo_01__executive_yoy_mom_budget_memo__2026-05-21__report_contract.json"
DEPTH_MODES = MARTS_DIR / "memo_depth_mode_catalog.parquet"

OUTPUT_INPUT_JSON = LLM_DIR / "deep_conclusion_input.json"
OUTPUT_DRAFT_MD = REPORTS_DIR / "deep_conclusion_draft.md"
OUTPUT_JUDGE_JSON = QA_DIR / "deep_conclusion_judge_review.json"
OUTPUT_JUDGE_MD = QA_DIR / "deep_conclusion_judge_review.md"

REQUIRED_HEADINGS = [
    "## Связный итоговый вывод",
    "## Что подтверждено данными",
    "## Что является расчётом",
    "## Что является интерпретацией",
    "## Что остаётся гипотезой",
    "## Связь аналитических блоков",
    "## Какие действия нужны",
    "## Ограничения",
]

FORBIDDEN_CAUSAL_PHRASES = [
    "причиной является",
    "является причиной",
    "доказана причина",
    "точно вызвано",
    "однозначно вызвано",
    "подтвержденная причина",
    "подтверждённая причина",
    "может быть связано",
    "могут быть связаны",
    "сезонными факторами",
    "изменениями в бизнес-стратегии",
    "может свидетельствовать",
    "свидетельствует о",
    "финансовое положение компании",
    "общую финансовую ситуацию",
    "chart localizes",
]


def snapshot(path: Path) -> dict[str, tuple[int, int]]:
    if not path.exists():
        return {}
    return {
        str(item.relative_to(PROJECT_ROOT)): (item.stat().st_mtime_ns, item.stat().st_size)
        for item in path.rglob("*")
        if item.is_file()
    }


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def compact_claim(claim: dict[str, Any]) -> dict[str, Any]:
    fields = [
        "claim_id",
        "claim_category",
        "section_id",
        "source_mart",
        "source_slice",
        "metric",
        "period",
        "evidence_id",
        "qa_status",
        "confidence_level",
        "limitation_text",
        "claim_basis",
        "risk_basis",
        "owner_candidate",
        "due_date",
        "action_status",
        "future_risk_flag",
        "denominator_status",
    ]
    return {field: claim.get(field, "") for field in fields}


def select_claims(package: dict[str, Any]) -> list[dict[str, Any]]:
    claims = [compact_claim(claim) for claim in package["claim_candidates"]]
    priority_sections = {
        "SEC_04_PLAN_FACT",
        "SEC_05_YOY",
        "SEC_06_MOM",
        "SEC_07_LOCALIZATION",
        "SEC_08_PLANNING_RISK",
        "SEC_09_IN_CONTEXT",
        "SEC_10_QA_LIMITATIONS",
        "SEC_11_ACTION_REGISTER",
        "SEC_12_FINAL_CONCLUSION",
    }
    selected = [claim for claim in claims if claim["section_id"] in priority_sections]
    selected.sort(key=lambda item: (item["section_id"], item["claim_category"], item["claim_id"]))
    return selected[:60]


def build_input_package() -> dict[str, Any]:
    package = read_json(DRAFT_PACKAGE)
    contract = read_json(REPORT_CONTRACT)
    depth_modes = pd.read_parquet(DEPTH_MODES).to_dict(orient="records") if DEPTH_MODES.exists() else []
    chart_catalog = pd.read_parquet(CHART_CATALOG)
    chart_records = chart_catalog[
        [
            "chart_id",
            "chart_name_ru",
            "memo_section",
            "metric",
            "grain",
            "period",
            "caption_ru",
            "limitation",
            "qa_status",
            "chart_role",
        ]
    ].to_dict(orient="records")
    evidence = pd.read_excel(EVIDENCE_MAP_XLSX, sheet_name="Evidence_Map").to_dict(orient="records")
    claims = select_claims(package)
    source_evidence_ids = sorted({str(claim["evidence_id"]) for claim in claims if claim.get("evidence_id")})
    selected_evidence = [
        row
        for row in evidence
        if str(row.get("Evidence ID", row.get("ID подтверждения", ""))) in source_evidence_ids
    ]
    input_package = {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "mode": "llm_synthesis_layer_only_no_metric_calculation",
        "memo_profile": package.get("memo_profile", "executive_yoy_mom_budget_memo"),
        "depth_mode": "depth_2_management_memo",
        "ollama": {
            "url": OLLAMA_URL,
            "models": OLLAMA_MODELS,
            "routing_note": OLLAMA_ROUTING_NOTE,
        },
        "rules": [
            "No new numbers.",
            "No unsupported causes.",
            "Planning risk is future risk, not actual execution.",
            "YoY and MoM remain separate.",
            "IN context means proportionality to inflow.",
            "Risk requires risk_basis.",
            "Low confidence cannot be final fact.",
            "Limitations must remain visible.",
        ],
        "required_output_blocks": [
            "Связный итоговый вывод",
            "Что подтверждено данными",
            "Что является расчётом",
            "Что является интерпретацией",
            "Что остаётся гипотезой",
            "Как связаны Plan-Fact, YoY, MoM, локализация, плановый риск и IN context",
            "Какие действия нужны",
            "Какие ограничения не позволяют усилить вывод",
        ],
        "depth_modes": depth_modes,
        "contract_rules": contract.get("global_claim_rules", []),
        "selected_claim_candidates": claims,
        "selected_evidence": selected_evidence,
        "chart_refs": chart_records,
        "limitations": sorted({claim.get("limitation_text", "") for claim in claims if claim.get("limitation_text")}),
        "risk_basis_values": sorted({claim.get("risk_basis", "") for claim in claims if claim.get("risk_basis")}),
        "action_candidates": [
            {
                "claim_id": claim["claim_id"],
                "evidence_id": claim["evidence_id"],
                "owner_candidate": claim["owner_candidate"],
                "due_date": claim["due_date"],
                "action_status": claim["action_status"],
                "risk_basis": claim["risk_basis"],
            }
            for claim in claims
            if claim.get("owner_candidate") or claim.get("action_status")
        ],
    }
    OUTPUT_INPUT_JSON.write_text(json.dumps(input_package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return input_package


def call_ollama_model(model: str, prompt: str, timeout: int = 300) -> tuple[str | None, str | None]:
    payload = json.dumps(
        {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.0, "num_predict": 1800},
        }
    ).encode("utf-8")
    req = request.Request(
        f"{OLLAMA_URL}/api/generate",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
        text = str(data.get("response", "")).strip()
        return (text, None) if text else (None, "empty_response")
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        return None, str(exc)


def generate_with_ollama(input_package: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    context_lines = []
    seen: set[str] = set()
    preferred_markers = [
        "PLAN_FACT_SCALE",
        "YOY_SHIFT",
        "MOM_INSTABILITY",
        "LOCALIZATION_CONCENTRATION",
        "PLANNING_RISK",
        "FLOW_PRESSURE",
        "SOURCE_QUALITY",
    ]
    ordered_claims = []
    for marker in preferred_markers:
        for claim in input_package["selected_claim_candidates"]:
            if marker in str(claim.get("evidence_id", "")):
                ordered_claims.append(claim)
                break
    ordered_claims.extend(input_package["selected_claim_candidates"])
    for claim in ordered_claims:
        evidence_id = str(claim.get("evidence_id", ""))
        if not evidence_id or evidence_id in seen:
            continue
        seen.add(evidence_id)
        context_lines.append(
            "- "
            + "; ".join(
                [
                    f"Evidence: {evidence_id}",
                    f"category: {claim.get('claim_category', '')}",
                    f"basis: {claim.get('claim_basis', '')}",
                    f"metric: {claim.get('metric', '')}",
                    f"risk_basis: {claim.get('risk_basis', '')}",
                    f"confidence: {claim.get('confidence_level', '')}",
                    f"owner: {claim.get('owner_candidate', '') or 'не указан'}",
                    f"due: {claim.get('due_date', '') or 'не указан'}",
                    f"status: {claim.get('action_status', '') or 'not_applicable'}",
                    f"limitation: {claim.get('limitation_text', '')}",
                ]
            )
        )
        if len(context_lines) >= 10:
            break
    compact_context = "\n".join(context_lines)
    prompt = f"""
Ты — LLM synthesis layer для управленческой записки. Пиши только на русском.

Задача: написать связный deep conclusion из deterministic evidence ниже.

Жесткие правила:
- Не добавляй новые числа, суммы, проценты, ранги или даты. Можно использовать только Evidence ID.
- Не упоминай периоды, даты, ранги, суммы, проценты и количества даже если они есть во входе.
- Не придумывай причины. Причинность можно писать только как гипотезу и только в разделе гипотез.
- Запрещены фразы: "может быть связано", "сезонные факторы", "изменения в бизнес-стратегии", "свидетельствует".
- Запрещены фразы: "финансовое положение компании", "Chart localizes".
- Запрещены фразы: "общая финансовая ситуация", "общую финансовую ситуацию".
- Все visible labels и текст должны быть на русском; английский допустим только для Plan-Fact, YoY, MoM, IN, OUT и Evidence ID.
- Разделяй DATA FACT, CALCULATION RESULT, INTERPRETATION, RECOMMENDATION, LIMITATION.
- Planning risk — будущий плановый риск, не фактическое исполнение.
- YoY и MoM держи раздельно.
- IN context означает пропорциональность расходов к притоку IN.
- Risk должен опираться на risk_basis.
- Low confidence не может быть финальным фактом.
- Ограничения должны быть явно видны.
- Рекомендации формулируй как действия проверки; если owner/due/status неполные, прямо отметь это.
- Не пиши decorative prose.
- Используй ТОЧНО указанные ниже заголовки, без переименований.
- Не пиши абзацы без Evidence.
- После каждого заголовка пиши только маркированные пункты. Никаких свободных абзацев.
- Даже под заголовком "Связный итоговый вывод" должен быть bullet с [INTERPRETATION] и Evidence.
- В каждом разделе должен быть минимум один пункт с category и Evidence.
- Каждый пункт после заголовка обязан начинаться с claim category:
  - [DATA FACT] ... Evidence: EV-...
  - [CALCULATION RESULT] ... Evidence: EV-...
  - [INTERPRETATION] ... Evidence: EV-...
  - [RECOMMENDATION] ... owner: ...; срок: ...; статус: ...; Evidence: EV-...
  - [LIMITATION] ... Evidence: EV-...
  - [HYPOTHESIS] ... Evidence: EV-...
- В разделе "Связь аналитических блоков" каждый пункт тоже обязан начинаться с [INTERPRETATION] и заканчиваться Evidence.
- В разделе гипотез обязательно напиши, что причины не подтверждены, если нет confirmed cause.
- В разделе действий обязательно используй слова: owner, срок, статус.
- В разделе связей обязательно упомяни: Plan-Fact, YoY, MoM, локализация, плановый риск, IN context, пропорциональность к притоку.
- В разделе связей обязательно добавь отдельный пункт про IN context: расходы рассматриваются как пропорциональность к притоку IN. Evidence: EV-FLOW_PRESSURE-00221
- В разделе планового риска обязательно напиши: это будущий плановый риск, не фактическое исполнение.

Обязательная структура Markdown:
## Связный итоговый вывод
## Что подтверждено данными
## Что является расчётом
## Что является интерпретацией
## Что остаётся гипотезой
## Связь аналитических блоков
## Какие действия нужны
## Ограничения

В каждом содержательном пункте ставь Evidence: <ID> из входа.
Не используй markdown tables.

INPUT_JSON:
{compact_context}
"""
    primary = model_for_role("analyst")
    text, error_text = call_ollama_model(primary, prompt)
    fallback_used = False
    model = primary
    if error_text:
        text, fallback_error = call_ollama_model(OLLAMA_FAST_FALLBACK_MODEL, prompt, timeout=180)
        fallback_used = text is not None
        model = OLLAMA_FAST_FALLBACK_MODEL if fallback_used else primary
        if not text:
            raise RuntimeError(f"Ollama generation failed: primary={error_text}; fallback={fallback_error}")
        error_text = f"primary_error:{error_text}"
    metadata = {
        "ollama_model": model,
        "ollama_primary_model": primary,
        "ollama_fallback_used": fallback_used,
        "ollama_error": error_text,
    }
    return text, metadata


def strip_ids_for_numeric_scan(text: str) -> str:
    text = re.sub(r"\b(?:EV|CH|SEC|EC|MOM|YOY|IN|OUT)[-_A-Z0-9]*\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\bdepth_[0-9]_[a-z_]+\b", " ", text)
    return text


def normalize_llm_markdown(text: str) -> str:
    replacements = {
        "[INTERPREТATION]": "[INTERPRETATION]",
        "[INTERPREТАЦИЯ]": "[INTERPRETATION]",
        "[INTERПРЕТАЦИЯ]": "[INTERPRETATION]",
        "[RECOMMENDАTION]": "[RECOMMENDATION]",
        "[СALCULATION RESULT]": "[CALCULATION RESULT]",
        "Chart localizes magnitude, not root cause.": "График локализует масштаб, но не определяет корневую причину.",
        "общую финансовую ситуацию": "локализованные изменения",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def judge_draft(markdown: str, input_package: dict[str, Any], metadata: dict[str, Any]) -> dict[str, Any]:
    evidence_ids = {str(claim["evidence_id"]) for claim in input_package["selected_claim_candidates"] if claim.get("evidence_id")}
    evidence_ids.update(str(row.get("Evidence ID", row.get("ID подтверждения", ""))) for row in input_package["selected_evidence"])
    evidence_ids = {item for item in evidence_ids if item and item != "nan"}
    headings_present = all(heading in markdown for heading in REQUIRED_HEADINGS)
    body_lines = [
        line.strip()
        for line in markdown.splitlines()
        if line.strip() and not line.startswith("#") and not line.startswith("---")
    ]
    material_lines = [line for line in body_lines if len(line) > 35]
    unsupported_lines = [
        line
        for line in material_lines
        if "Evidence:" in line and not any(evidence_id in line for evidence_id in evidence_ids)
    ]
    lines_missing_evidence = [
        line
        for line in material_lines
        if not line.startswith(("Ограничение:", "Гипотеза:", "Важно:")) and "Evidence:" not in line
    ]
    numeric_scan = strip_ids_for_numeric_scan(markdown)
    new_numeric_claims = re.findall(r"(?<![A-Za-zА-Яа-я])[-+]?\d+(?:[.,]\d+)?\s*(?:%|EUR|евро|млн|тыс\.?|k|M)?", numeric_scan)
    lower = markdown.lower()
    forbidden_causal = [phrase for phrase in FORBIDDEN_CAUSAL_PHRASES if phrase in lower]
    planning_ok = "плановый риск" in lower and "будущ" in lower and "фактическ" in lower
    yoy_mom_ok = "yoy" in lower and "mom" in lower and lower.find("yoy") != lower.find("mom")
    in_ok = "in" in lower and "пропорциональ" in lower and "приток" in lower
    hypotheses_marked = "## Что остаётся гипотезой" in markdown and ("Гипотеза" in markdown or "[HYPOTHESIS]" in markdown)
    limitations_visible = "## Ограничения" in markdown and ("не позволяет" in lower or "огранич" in lower)
    action_section = markdown.split("## Какие действия нужны", 1)[-1].split("## Ограничения", 1)[0]
    action_ok = all(token in action_section.lower() for token in ["owner", "срок", "статус"])
    checks = {
        "required_headings_present": headings_present,
        "unsupported_claims_zero": len(unsupported_lines) == 0 and len(lines_missing_evidence) == 0,
        "new_numeric_claims_zero": len(new_numeric_claims) == 0,
        "hypotheses_clearly_marked": hypotheses_marked,
        "recommendations_have_owner_due_status_where_available": action_ok,
        "conclusion_does_not_exceed_evidence": len(forbidden_causal) == 0 and len(unsupported_lines) == 0,
        "planning_risk_future_not_actual_execution": planning_ok,
        "yoy_and_mom_separate": yoy_mom_ok,
        "in_context_proportionality_to_inflow": in_ok,
        "limitations_visible": limitations_visible,
        "ollama_used": bool(metadata.get("ollama_model")),
    }
    return {
        "created_at": datetime.now(timezone.utc).isoformat(),
        "qa_status": "pass" if all(checks.values()) else "fail",
        "judge_verdict": "accept" if all(checks.values()) else "revise",
        "quality_score": 8 if all(checks.values()) else 6,
        "confidence_score": 8 if all(checks.values()) else 6,
        "ollama": metadata,
        "checks": checks,
        "unsupported_claims": unsupported_lines + lines_missing_evidence,
        "new_numeric_claims": new_numeric_claims,
        "forbidden_causal_phrases": forbidden_causal,
        "residual_risks": [
            "LLM synthesis is bounded by deterministic evidence but still requires human review before replacing accepted memo text.",
            "No metrics were calculated in this layer.",
        ],
    }


def write_outputs(markdown: str, judge: dict[str, Any]) -> None:
    OUTPUT_DRAFT_MD.write_text(markdown.strip() + "\n", encoding="utf-8")
    OUTPUT_JUDGE_JSON.write_text(json.dumps(judge, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    lines = [
        "# Deep Conclusion Judge Review",
        "",
        f"judge_verdict: {judge['judge_verdict']}",
        f"qa_status: {judge['qa_status']}",
        f"quality_score: {judge['quality_score']}",
        f"confidence_score: {judge['confidence_score']}",
        f"ollama_model: {judge['ollama'].get('ollama_model')}",
        "",
        "## Checks",
        *[f"- {key}: {'pass' if value else 'fail'}" for key, value in judge["checks"].items()],
        "",
        "## Unsupported Claims",
        *([f"- {line}" for line in judge["unsupported_claims"]] or ["- none"]),
        "",
        "## New Numeric Claims",
        *([f"- {item}" for item in judge["new_numeric_claims"]] or ["- none"]),
        "",
        "## Residual Risks",
        *[f"- {risk}" for risk in judge["residual_risks"]],
    ]
    OUTPUT_JUDGE_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    memo_profile = "executive_yoy_mom_budget_memo"
    depth_mode = "depth_2_management_memo"
    log_progress(memo_profile=memo_profile, depth_mode=depth_mode, stage="deep_conclusion_input", status="start")
    raw_before = snapshot(RAW_DIR)
    stage_before = snapshot(STAGE_DIR)
    marts_before = snapshot(MARTS_DIR)
    charts_before = snapshot(CHARTS_DIR)
    input_package = build_input_package()
    log_progress(memo_profile=memo_profile, depth_mode=depth_mode, stage="ollama_deep_conclusion_generation", status="start")
    markdown, metadata = generate_with_ollama(input_package)
    log_progress(memo_profile=memo_profile, depth_mode=depth_mode, stage="ollama_deep_conclusion_generation", status="done", details={"model": metadata["ollama_model"]})
    markdown = normalize_llm_markdown(markdown)
    log_progress(memo_profile=memo_profile, depth_mode=depth_mode, stage="deep_conclusion_judge", status="start")
    judge = judge_draft(markdown, input_package, metadata)
    judge["preservation_checks"] = {
        "raw_untouched": raw_before == snapshot(RAW_DIR),
        "stage_untouched": stage_before == snapshot(STAGE_DIR),
        "mart_formulas_untouched": marts_before == snapshot(MARTS_DIR),
        "chart_data_untouched": charts_before == snapshot(CHARTS_DIR),
    }
    if not all(judge["preservation_checks"].values()):
        judge["qa_status"] = "fail"
        judge["judge_verdict"] = "block"
    write_outputs(markdown, judge)
    log_progress(memo_profile=memo_profile, depth_mode=depth_mode, stage="deep_conclusion_judge", status=judge["qa_status"], details={"judge_verdict": judge["judge_verdict"]})
    print(json.dumps({"qa_status": judge["qa_status"], "judge_verdict": judge["judge_verdict"], "ollama_model": metadata["ollama_model"]}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
