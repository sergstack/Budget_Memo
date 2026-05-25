from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd


TECHNICAL_ID_RE = re.compile(r"\b(?:EV-[A-Z0-9_-]+|CH_[A-Z0-9_]+|slice_[A-Za-z0-9_]+|mart_[A-Za-z0-9_]+)\b")
NUMBER_RE = re.compile(r"(?<![A-Za-zА-Яа-я])[-+]?\d+(?:[.,]\d+)?\s*(?:млн|тыс\.?|%|EUR|евро|ранг)?", re.IGNORECASE)

STRONG_CAUSALITY = [
    "причина",
    "из-за",
    "привело к",
    "обусловлено",
    "доказано",
]
SOFT_CAUSALITY = [
    "может указывать",
    "требует проверки",
    "предварительно",
    "гипотеза",
]
PLANNING_RISK_AS_FACT = [
    "плановый риск является фактом исполнения",
    "плановый риск как факт исполнения",
    "плановый риск подтверждает перерасход",
    "плановый риск подтверждает экономию",
]
TIMING_CONFIRMED = [
    "подтвержденный timing",
    "подтверждённый timing",
    "срок переноса подтвержден",
    "срок переноса подтверждён",
]
FINAL_ACTION_TERMS = [
    "финальный план действий",
    "назначить",
    "сделать до",
    "ответственный подтверждён",
    "ответственный подтвержден",
]
ALLOWED_ACTION_TERMS = [
    "кандидат проверки",
    "требует подтверждения срока и статуса",
    "owner route = цфо",
    "маршрут проверки = цфо",
]
ENGLISH_TERMS = [
    "accepted package",
    "action memo",
    "candidate action",
    "candidate_only",
    "executive summary",
    "executive verdict",
    "executive overview",
    "экзекутивный обзор",
    "экзекутивное резюме",
    "экзекутивный вывод",
    "source mix",
    "row type",
    "gross abs delta",
    "net delta",
    "logic workbook",
    "chart manifest",
    "fallback",
    "pipeline",
    "candidate checks",
    "final action plan",
    "over-execution",
    "under-execution",
    "cfo x article",
    "management_release_candidate_with_candidate_actions",
]

GENERIC_CHART_PLACEHOLDERS = [
    "зона проверки по данным контрольного пакета",
    "график используется как визуальная опора",
    "локализует приоритет проверки",
]


@dataclass
class QaContext:
    allowed_numbers: set[str]
    due_date_status_confirmed: bool = False
    timing_confirmed: bool = False
    confirmed_cause_evidence: bool = False
    memo_profile: str = ""
    allow_readable_main_with_appendix_evidence: bool = True


def normalize_number_token(value: str) -> str:
    value = value.strip().lower().replace(",", ".")
    value = re.sub(r"\s+", " ", value)
    value = value.replace("тыс. eur", "тыс eur")
    value = value.replace("тыс.", "тыс")
    value = value.replace("млн eur", "млн")
    value = value.replace("тыс eur", "тыс")
    return value


def format_business_number(value: float, unit: str = "") -> list[str]:
    sign = "-" if value < 0 else ""
    abs_value = abs(float(value))
    if unit.upper() == "EUR":
        if abs_value >= 1_000_000:
            formatted = f"{sign}{abs_value / 1_000_000:.2f}".replace(".", ",") + " млн EUR"
        elif abs_value >= 1_000:
            formatted = f"{sign}{abs_value / 1_000:.1f}".replace(".", ",") + " тыс. EUR"
        else:
            formatted = f"{sign}{abs_value:.2f}".replace(".", ",") + " EUR"
        unsigned = formatted.lstrip("-")
        return [formatted, formatted.replace("-", "−"), unsigned]
    return [str(value)]


def format_business_percent(value: float) -> list[str]:
    pct = float(value) * 100 if abs(float(value)) <= 10 else float(value)
    formatted = f"{pct:.1f}%".replace(".", ",")
    return [formatted]


def extract_numbers(text: str) -> set[str]:
    text = TECHNICAL_ID_RE.sub(" ", text)
    text = re.sub(r"\bmemo_\d+\b", " ", text, flags=re.IGNORECASE)
    text = re.sub(r"\b\d{4}-\d{2}(?:-\d{2})?\b", " ", text)
    return {normalize_number_token(match.group(0)) for match in NUMBER_RE.finditer(text)}


def load_allowed_numbers(paths: list[Path]) -> set[str]:
    allowed: set[str] = set()
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in {".md", ".txt", ".json", ".csv"}:
            text = path.read_text(encoding="utf-8")
        elif path.suffix.lower() == ".xlsx":
            frames = pd.read_excel(path, sheet_name=None)
            text = "\n".join(df.to_csv(index=False) for df in frames.values())
            for df in frames.values():
                for column in df.columns:
                    column_name = str(column).lower()
                    if column_name.endswith("_pct") or column_name.endswith("_ratio"):
                        values = pd.to_numeric(df[column], errors="coerce").dropna()
                        for value in values:
                            for formatted in format_business_percent(float(value)):
                                allowed.add(normalize_number_token(formatted))
                        continue
                    if not column_name.endswith("_eur"):
                        continue
                    values = pd.to_numeric(df[column], errors="coerce").dropna()
                    for value in values:
                        allowed.add(normalize_number_token(f"{value:.2f} EUR"))
                        for formatted in format_business_number(float(value), "EUR"):
                            allowed.add(normalize_number_token(formatted))
        else:
            text = ""
        allowed.update(extract_numbers(text))
    return allowed


def split_main_and_appendix(text: str) -> tuple[str, str]:
    match = re.search(r"^##\s*(?:Приложение|Appendix|Evidence|Источник|Source)", text, flags=re.IGNORECASE | re.MULTILINE)
    if not match:
        return text, ""
    return text[: match.start()], text[match.start() :]


def line_has_evidence_or_label(line: str) -> bool:
    lowered = line.lower()
    return (
        "evidence:" in lowered
        or "[evid:" in lowered
        or "id подтверждения" in lowered
        or "источник:" in lowered
        or "source_file:" in lowered
        or "[interpretation]" in lowered
        or "[limitation]" in lowered
        or "[hypothesis]" in lowered
        or "ограничение" in lowered
        or "гипотеза" in lowered
        or "требует проверки" in lowered
    )


def important_claim_lines(text: str) -> list[str]:
    lines = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or line.startswith("|") or line.startswith("!") or line == "---":
            continue
        if len(line) >= 45:
            lines.append(line)
    return lines


def find_unsupported_claims(text: str) -> list[str]:
    unsupported = []
    main, appendix = split_main_and_appendix(text)
    appendix_has_evidence = bool(
        appendix
        and (
            re.search(r"\bEV-[A-Z0-9_-]+\b", appendix)
            or "evidence" in appendix.lower()
            or "источник" in appendix.lower()
            or "source" in appendix.lower()
        )
    )
    for line in important_claim_lines(main):
        if not line_has_evidence_or_label(line):
            if appendix_has_evidence:
                continue
            unsupported.append(line)
    return unsupported


def find_readability_violations(text: str) -> list[str]:
    main, _ = split_main_and_appendix(text)
    lowered = main.lower()
    placeholder_hits = [term for term in GENERIC_CHART_PLACEHOLDERS if term in lowered]
    claim_lines = important_claim_lines(main)
    if not claim_lines:
        return ["empty_or_too_short_executive_body"]
    source_prefixed = [
        line
        for line in claim_lines
        if line.lower().startswith(("источник:", "ограничение:"))
    ]
    if placeholder_hits:
        return [f"generic_chart_placeholder:{term}" for term in placeholder_hits]
    if len(source_prefixed) >= 5 and len(source_prefixed) / max(len(claim_lines), 1) > 0.45:
        return ["executive_body_too_label_driven"]
    return []


def find_causality_violations(text: str, confirmed_cause_evidence: bool) -> list[str]:
    if confirmed_cause_evidence:
        return []
    violations = []
    for line in text.splitlines():
        lowered = line.lower()
        if "не причина" in lowered or "не подтверждает причину" in lowered:
            continue
        if any(term in lowered for term in STRONG_CAUSALITY) and not any(term in lowered for term in SOFT_CAUSALITY):
            violations.append(line.strip())
    return [item for item in violations if item]


def find_action_maturity_violations(text: str, due_date_status_confirmed: bool) -> list[str]:
    if due_date_status_confirmed:
        return []
    violations = []
    for line in text.splitlines():
        lowered = line.lower()
        if any(term in lowered for term in FINAL_ACTION_TERMS) and not any(term in lowered for term in ALLOWED_ACTION_TERMS):
            violations.append(line.strip())
    return [item for item in violations if item]


def find_language_violations(text: str) -> list[str]:
    main, _ = split_main_and_appendix(text)
    violations = []
    lowered = main.lower()
    for term in ENGLISH_TERMS:
        if term in lowered:
            violations.append(term)
    if re.search(r"\bюзер(?:ы|ов|ам|ами|ах)?\b", lowered):
        violations.append("юзер")
    if "юзерам" in lowered:
        violations.append("юзерам")
    if "др [расшифровать]" in lowered:
        violations.append("ДР [расшифровать]")
    violations.extend(TECHNICAL_ID_RE.findall(main))
    return sorted(set(violations))


def find_planning_risk_violations(text: str) -> list[str]:
    lowered = text.lower()
    violations = [term for term in PLANNING_RISK_AS_FACT if term in lowered]
    planning_mentions = "плановый риск" in lowered
    if planning_mentions and not ("не факт исполнения" in lowered or "будущий бюджетный риск" in lowered):
        violations.append("planning_risk_missing_required_limitation")
    return violations


def find_timing_violations(text: str, timing_confirmed: bool) -> list[str]:
    if timing_confirmed:
        return []
    lowered = text.lower()
    return [term for term in TIMING_CONFIRMED if term in lowered]


def find_formula_semantics_violations(text: str, memo_profile: str) -> list[str]:
    if memo_profile and memo_profile != "monthly_plan_fact_memo":
        return []
    lowered = text.lower()
    violations = []
    if "delta eur = plan eur - fact eur" not in lowered:
        violations.append("missing_or_changed_delta_formula")
    if "positive delta = fact below plan" not in lowered and "положительная delta = факт ниже плана" not in lowered:
        violations.append("missing_positive_delta_semantics")
    if "negative delta = fact above plan" not in lowered and "отрицательная delta = факт выше плана" not in lowered:
        violations.append("missing_negative_delta_semantics")
    if "abs delta" in lowered and not ("scale" in lowered or "масштаб" in lowered):
        violations.append("abs_delta_not_labeled_as_scale")
    return violations


def limitation_visibility_status(text: str) -> str:
    lowered = text.lower()
    has_limitations = "## ограничения" in lowered or "## limitations" in lowered
    comments_ok = "семантический анализ причин не выполнялся" in lowered or "комментарии" not in lowered
    action_ok = "кандидат" in lowered and ("срок" in lowered and "статус" in lowered)
    direction_ok = "direction" not in lowered or "не блокирует" in lowered or "optional" in lowered
    return "pass" if has_limitations and comments_ok and action_ok and direction_ok else "fail"


def find_chart_caption_violations(text: str) -> list[str]:
    violations = []
    for line in text.splitlines():
        stripped = line.strip()
        if not (stripped.lower().startswith("график:") or stripped.lower().startswith("caption:")):
            continue
        lowered = stripped.lower()
        if "причина" in lowered and "не подтверж" not in lowered and "не причина" not in lowered:
            violations.append(stripped)
        required = ["источник", "метрик", "период", "огранич"]
        missing = [token for token in required if token not in lowered]
        if missing:
            violations.append(f"{stripped} | missing: {', '.join(missing)}")
        if any(term in lowered for term in ENGLISH_TERMS):
            violations.append(stripped)
    return violations


def judge_verdict_gate(judge_path: Path | None) -> tuple[str, list[str]]:
    if not judge_path:
        return "not_checked", []
    data = json.loads(judge_path.read_text(encoding="utf-8"))
    verdict = str(data.get("verdict", "")).lower()
    if verdict == "accept":
        return "pass", []
    return "fail", [f"judge_verdict={verdict or 'missing'}"]


def validate_text(text: str, context: QaContext, judge_path: Path | None = None) -> dict[str, Any]:
    found_numbers = extract_numbers(text)
    new_numbers = sorted(found_numbers - context.allowed_numbers)
    unsupported_claims = find_unsupported_claims(text)
    causality = find_causality_violations(text, context.confirmed_cause_evidence)
    action = find_action_maturity_violations(text, context.due_date_status_confirmed)
    language = find_language_violations(text)
    planning = find_planning_risk_violations(text)
    timing = find_timing_violations(text, context.timing_confirmed)
    formula = find_formula_semantics_violations(text, context.memo_profile)
    limitation_status = limitation_visibility_status(text)
    chart = find_chart_caption_violations(text)
    readability = find_readability_violations(text)
    judge_status, judge_issues = judge_verdict_gate(judge_path)
    failures = [
        new_numbers,
        unsupported_claims,
        causality,
        action,
        language,
        planning,
        timing,
        formula,
        chart,
        readability,
        judge_issues,
    ]
    if limitation_status != "pass":
        failures.append(["limitation_visibility_status=fail"])
    qa_status = "fail" if any(failures) else "pass"
    return {
        "qa_status": qa_status,
        "unsupported_claims": unsupported_claims,
        "new_numeric_claims": new_numbers,
        "causality_violations": causality,
        "action_maturity_violations": action,
        "language_violations": language,
        "planning_risk_violations": planning,
        "timing_violations": timing,
        "formula_semantics_violations": formula,
        "chart_caption_violations": chart,
        "readability_violations": readability,
        "limitation_visibility_status": limitation_status,
        "judge_verdict_gate": judge_status,
        "judge_verdict_issues": judge_issues,
        "recommendation": "accept" if qa_status == "pass" else "block",
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Validate Ollama-generated memo narrative against deterministic QA rules.")
    parser.add_argument("memo_output", type=Path)
    parser.add_argument("--allowed-source", action="append", default=[], type=Path)
    parser.add_argument("--judge-review", type=Path)
    parser.add_argument("--memo-profile", default="")
    parser.add_argument("--due-date-status-confirmed", action="store_true")
    parser.add_argument("--timing-confirmed", action="store_true")
    parser.add_argument("--confirmed-cause-evidence", action="store_true")
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    text = args.memo_output.read_text(encoding="utf-8")
    context = QaContext(
        allowed_numbers=load_allowed_numbers(args.allowed_source),
        due_date_status_confirmed=args.due_date_status_confirmed,
        timing_confirmed=args.timing_confirmed,
        confirmed_cause_evidence=args.confirmed_cause_evidence,
        memo_profile=args.memo_profile,
    )
    result = validate_text(text, context, args.judge_review)
    payload = json.dumps(result, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
    print(payload, end="")
    raise SystemExit(0 if result["qa_status"] == "pass" else 1)


if __name__ == "__main__":
    main()
