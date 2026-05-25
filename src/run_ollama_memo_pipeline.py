from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Callable
from urllib import error, request

from src.qa_ollama_outputs import QaContext, load_allowed_numbers, validate_text


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_QA_DIR = PROJECT_ROOT / "07_qa" / "llm_narrative_qa"
DEFAULT_ROUTING = PROJECT_ROOT / "config" / "ollama_memo_routing.json"


class OllamaUnavailable(RuntimeError):
    pass


class OllamaText(str):
    def __new__(cls, value: str, metadata: dict):
        obj = str.__new__(cls, value)
        obj.metadata = metadata
        return obj


@dataclass
class PipelineInputs:
    memo_profile: str
    depth_mode: str
    accepted_package: Path
    claim_candidates: Path
    evidence_map: Path
    chart_catalog: Path
    report_contract: Path
    package_qa: Path
    output_dir: Path = DEFAULT_QA_DIR
    accepted_final_docx: Path | None = None
    accepted_final_md: Path | None = None
    due_date_status_confirmed: bool = False
    timing_confirmed: bool = False
    confirmed_cause_evidence: bool = False


def read_text_if_exists(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.exists() else ""


def load_routing(path: Path = DEFAULT_ROUTING) -> dict:
    if not path.exists():
        raise FileNotFoundError(f"Missing Ollama routing config: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def role_config(routing: dict, role: str) -> dict:
    for item in routing.get("roles", []):
        if item.get("role") == role:
            return item
    raise KeyError(f"Missing role in routing config: {role}")


def call_ollama(url: str, model: str, prompt: str, options: dict, timeout: int = 300, response_format: str | None = None) -> str:
    body = {"model": model, "prompt": prompt, "stream": False, "options": options}
    if response_format:
        body["format"] = response_format
    payload = json.dumps(body).encode("utf-8")
    req = request.Request(f"{url}/api/generate", data=payload, headers={"Content-Type": "application/json"}, method="POST")
    try:
        with request.urlopen(req, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise OllamaUnavailable(str(exc)) from exc
    text = str(data.get("response", "")).strip()
    if not text:
        raise OllamaUnavailable("empty_response")
    return text


def default_ollama_client(role: str, prompt: str, routing: dict) -> str:
    cfg = role_config(routing, role)
    url = routing.get("ollama_url", "http://127.0.0.1:11434")
    primary_model = cfg["primary_model"]
    fallback_model = cfg.get("fallback_model", primary_model)
    options = {
        "temperature": cfg.get("temperature", 0.0),
        "top_p": cfg.get("top_p", 0.9),
        "num_predict": cfg.get("max_tokens", 2500),
    }
    response_format = "json" if role == "judge" else None
    try:
        text = call_ollama(url, primary_model, prompt, options, response_format=response_format)
        return OllamaText(
            text,
            {
                "role": role,
                "endpoint": url,
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "fallback_used": False,
                "fallback_reason": "",
                "final_model": primary_model,
            },
        )
    except OllamaUnavailable as primary_exc:
        try:
            text = call_ollama(url, fallback_model, prompt, options, response_format=response_format)
        except OllamaUnavailable as fallback_exc:
            raise OllamaUnavailable(
                json.dumps(
                    {
                        "role": role,
                        "endpoint": url,
                        "primary_model": primary_model,
                        "fallback_model": fallback_model,
                        "primary_error": str(primary_exc),
                        "fallback_error": str(fallback_exc),
                    },
                    ensure_ascii=False,
                )
            ) from fallback_exc
        return OllamaText(
            text,
            {
                "role": role,
                "endpoint": url,
                "primary_model": primary_model,
                "fallback_model": fallback_model,
                "fallback_used": True,
                "fallback_reason": "primary_unavailable",
                "primary_error": str(primary_exc),
                "final_model": fallback_model,
            },
        )


def model_metadata(value: str) -> dict:
    return dict(getattr(value, "metadata", {}))


def call_judge_with_schema(prompt: str, routing: dict, ollama_client: Callable[[str, str, dict], str]) -> tuple[str, dict]:
    response = ollama_client("judge", prompt, routing)
    parsed = parse_judge_json(response)
    response_meta = model_metadata(response)
    if response_meta:
        parsed["model_metadata"] = response_meta
    if not judge_schema_invalid(parsed):
        parsed.setdefault("schema_status", "valid")
        parsed.setdefault("fallback_used", False)
        parsed.setdefault("fallback_reason", "")
        return response, parsed
    if ollama_client is not default_ollama_client:
        parsed.setdefault("schema_status", "invalid")
        parsed.setdefault("fallback_used", False)
        parsed.setdefault("fallback_reason", "mock_or_custom_client_no_fallback")
        return response, parsed
    cfg = role_config(routing, "judge")
    options = {
        "temperature": cfg.get("temperature", 0.0),
        "top_p": cfg.get("top_p", 0.8),
        "num_predict": cfg.get("max_tokens", 2500),
    }
    fallback_model = cfg.get("fallback_model")
    if fallback_model and fallback_model != cfg.get("primary_model"):
        fallback_response = call_ollama(
            routing.get("ollama_url", "http://127.0.0.1:11434"),
            fallback_model,
            prompt,
            options,
            response_format="json",
        )
        fallback_parsed = parse_judge_json(fallback_response)
        fallback_parsed["schema_status"] = "valid" if not judge_schema_invalid(fallback_parsed) else "invalid"
        fallback_parsed["fallback_used"] = True
        fallback_parsed["fallback_reason"] = "schema_recovery"
        fallback_parsed["judge_fallback_used"] = fallback_model
        fallback_parsed["model_metadata"] = {
            "role": "judge",
            "endpoint": routing.get("ollama_url", "http://127.0.0.1:11434"),
            "primary_model": cfg.get("primary_model"),
            "fallback_model": fallback_model,
            "fallback_used": True,
            "fallback_reason": "schema_recovery",
            "final_model": fallback_model,
        }
        return fallback_response, fallback_parsed
    parsed.setdefault("schema_status", "invalid")
    parsed.setdefault("fallback_used", False)
    parsed.setdefault("fallback_reason", "schema_invalid_no_fallback_model")
    return response, parsed


def build_input_package(inputs: PipelineInputs) -> str:
    parts = [
        "# Accepted deterministic package",
        read_text_if_exists(inputs.accepted_package),
        "# Claim candidates",
        read_text_if_exists(inputs.claim_candidates),
        "# Evidence map",
        read_text_if_exists(inputs.evidence_map),
        "# Chart catalog",
        read_text_if_exists(inputs.chart_catalog),
        "# Report contract",
        read_text_if_exists(inputs.report_contract),
        "# Package QA",
        read_text_if_exists(inputs.package_qa),
    ]
    return "\n\n".join(parts)


TECHNICAL_INPUT_SECTION_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*(?:\d+[\.)]\s*)?(?:"
    r"Step-by-Step Guide|Compute Selected Closed Month|Create Excel Workbook|"
    r"Create Excel Workbook Tabs|Generate Charts|Prepare Evidence Map|"
    r"Output Folder Layout|Example Code Snippets|Python Code|Final Steps|"
    r"Review and Validate|Save and Store|QA Check|Implementation Steps|"
    r"Build Checklist|Package QA|Files To Inspect|Files Allowed To Modify|"
    r"Forbidden Actions|Rollback Plan|Tests / Smoke Checks"
    r")\b",
    flags=re.IGNORECASE,
)


TECHNICAL_LINE_PATTERNS = [
    re.compile(pattern, flags=re.IGNORECASE)
    for pattern in [
        r"\bimport\s+\w+",
        r"\bfrom\s+\w+\s+import\b",
        r"\bpd\.",
        r"\bplt\.",
        r"\bwith\s+pd\.",
        r"\.sort_values\b",
        r"\.head\(",
        r"\.read_parquet\b",
        r"\.to_excel\b",
        r"\.savefig\b",
        r"/Users/",
        r"\bsrc/",
        r"\b03_marts/",
        r"\b02_stage/",
        r"\bfolder\b",
        r"_folder\b",
        r"\bfolder_",
        r"\bimplementation\b",
        r"\bdebug\b",
    ]
]


def is_technical_line(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if re.search(r"!\[[^\]]*\]\([^)]*\)", stripped):
        return True
    if re.search(r"\b(?:[A-Za-z0-9_.-]+/){1,}[A-Za-z0-9_. -]+", stripped):
        return True
    return any(pattern.search(stripped) for pattern in TECHNICAL_LINE_PATTERNS)


def sanitize_llm_input_text(markdown: str) -> tuple[str, list[dict]]:
    lines = markdown.splitlines()
    kept: list[str] = []
    removed: list[dict] = []
    skipping_level: int | None = None
    in_code_block = False
    for line_no, line in enumerate(lines, start=1):
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            removed.append({"line": line_no, "reason": "code_block", "text": stripped[:180]})
            continue
        if in_code_block:
            removed.append({"line": line_no, "reason": "code_block", "text": stripped[:180]})
            continue
        heading = re.match(r"^(\s{0,3}#{1,6})\s+", line)
        if heading:
            level = len(heading.group(1).strip())
            if TECHNICAL_INPUT_SECTION_RE.match(line):
                skipping_level = level
                removed.append({"line": line_no, "reason": "technical_section", "text": stripped[:180]})
                continue
            if skipping_level is not None and level <= skipping_level:
                skipping_level = None
        if skipping_level is not None:
            removed.append({"line": line_no, "reason": "technical_section_body", "text": stripped[:180]})
            continue
        if is_technical_line(line):
            removed.append({"line": line_no, "reason": "technical_or_path_line", "text": stripped[:180]})
            continue
        kept.append(line)
    return "\n".join(kept).strip() + "\n", removed


def build_sanitized_input_package(inputs: PipelineInputs) -> tuple[str, dict]:
    raw_parts = [
        ("accepted_package", inputs.accepted_package, "# Accepted deterministic package"),
        ("claim_candidates", inputs.claim_candidates, "# Claim candidates"),
        ("evidence_map", inputs.evidence_map, "# Evidence map"),
        ("chart_catalog", inputs.chart_catalog, "# Chart catalog"),
        ("report_contract", inputs.report_contract, "# Report contract"),
        ("package_qa", inputs.package_qa, "# Package QA"),
    ]
    sanitized_parts = []
    removed_by_source = []
    for source_id, path, heading in raw_parts:
        sanitized, removed = sanitize_llm_input_text(read_text_if_exists(path))
        sanitized_parts.extend([heading, sanitized])
        if removed:
            removed_by_source.append(
                {
                    "source_id": source_id,
                    "source_file": str(path),
                    "removed_count": len(removed),
                    "removed_fragments": removed[:40],
                }
            )
    package = "\n\n".join(sanitized_parts).strip() + "\n"
    report = {
        "sanitization_status": "pass",
        "rule": "exclude implementation snippets, code blocks, local paths, folder-layout notes, and debug/build context from LLM judge package",
        "removed_sources_count": len(removed_by_source),
        "removed_by_source": removed_by_source,
    }
    return package, report


def judge_input_package(
    package: str,
    registry: list[dict],
    matrix: list[dict],
    evidence_backed_draft: str,
    preflight: dict | None = None,
) -> str:
    ready = [row for row in matrix if row["judge_ready"]]
    not_ready = [row for row in matrix if not row["judge_ready"]]
    secondary_only = [row for row in matrix if row["evidence_level"] == "secondary_narrative"]
    compact_matrix = {
        "claims_total": len(matrix),
        "judge_ready_claims": len(ready),
        "not_ready_claims": len(not_ready),
        "claims_with_primary_evidence": sum(1 for row in matrix if str(row["evidence_level"]).startswith("primary_")),
        "claims_with_secondary_narrative_only": len(secondary_only),
        "blocking_claims_count": len(not_ready),
        "not_ready": not_ready[:20],
        "secondary_narrative_only": secondary_only[:20],
        "ready_sample": ready[:40],
    }
    preflight_summary = {}
    if preflight:
        preflight_summary = {
            "preflight_status": preflight.get("preflight_status"),
            "blocking_claims_count": preflight.get("blocking_claims_count"),
            "claims_total": preflight.get("claims_total"),
            "claims_judge_ready": preflight.get("claims_judge_ready"),
            "claims_with_primary_evidence": preflight.get("claims_with_primary_evidence"),
            "claims_with_secondary_narrative_only": preflight.get("claims_with_secondary_narrative_only"),
            "unsupported_claims": preflight.get("unsupported_claims"),
            "top_blocking_claims": preflight.get("top_blocking_claims", [])[:10],
            "numeric_claims_without_metric_ref": preflight.get("numeric_claims_without_metric_ref", [])[:10],
            "fact_or_calculation_secondary_only": preflight.get("fact_or_calculation_secondary_only", [])[:10],
            "recommendation_secondary_only": preflight.get("recommendation_secondary_only", [])[:10],
        }
    return "\n\n".join(
        [
            "# Deterministic source summary",
            package[:12000],
            "# Source registry",
            json.dumps(registry, ensure_ascii=False),
            "# Deterministic preflight summary",
            json.dumps(preflight_summary, ensure_ascii=False),
            "# Claim evidence matrix summary",
            json.dumps(compact_matrix, ensure_ascii=False),
            "# Evidence-backed draft",
            evidence_backed_draft[:24000],
        ]
    )


def judge_prompt_text(base_prompt: str, payload: str) -> str:
    schema = {
        "verdict": "accept|revise|block",
        "qa_status": "pass|revise|fail",
        "unsupported_claims": [],
        "new_numeric_claims": [],
        "unsupported_causality": [],
        "action_issues": [],
        "confidence_issues": [],
        "timing_issues": [],
        "planning_risk_issues": [],
        "limitation_issues": [],
        "chart_caption_issues": [],
        "production_readiness_issues": [],
        "evidence_level_issues": [],
        "recommendation_basis_issues": [],
        "schema_status": "valid|invalid",
        "fallback_used": False,
        "fallback_reason": "",
        "required_revisions": [],
        "residual_risks": [],
    }
    return (
        f"{base_prompt}\n\n"
        "CRITICAL OUTPUT RULE: return exactly one valid JSON object matching this schema. "
        "Do not use keys such as query, summary, answer or response. Do not return Markdown.\n"
        "EVIDENCE RULES: FACT and CALCULATION claims require primary evidence. Numeric claims require metric_ref. "
        "Recommendations require a sourced FACT or INTERPRETATION basis. Secondary narrative alone is not enough "
        "for facts, calculations, executive summary claims, or recommendation basis. Unsupported claims must not "
        "appear in executive summary, conclusion, or recommendations.\n"
        "PREFLIGHT CONSISTENCY RULE: the deterministic preflight summary is authoritative for evidence readiness. "
        "If preflight reports blocking_claims_count=0 and claims_with_secondary_narrative_only=0, do not state that "
        "claims are secondary-narrative-only unless you cite exact claim_id and evidence_level from the provided "
        "claim evidence matrix in evidence_level_issues or recommendation_basis_issues. Generic secondary-only "
        "revisions without claim_id are invalid.\n"
        "FALLBACK RULE: fallback judge may only recover invalid schema and must not override an unfavorable valid verdict.\n"
        "If unsupported_claims, new_numeric_claims, unsupported_causality, action_issues, confidence_issues, "
        "timing_issues, planning_risk_issues, limitation_issues, chart_caption_issues and "
        "production_readiness_issues, evidence_level_issues and recommendation_basis_issues are all empty, "
        "verdict must be accept and required_revisions must be empty. "
        "Do not add generic required_revisions unless they correspond to a concrete issue listed above.\n"
        f"{json.dumps(schema, ensure_ascii=False)}\n\n"
        f"{payload}\n\n"
        "Return only the JSON object now."
    )


def find_claim(rows: list[dict], contains: list[str]) -> dict | None:
    for row in rows:
        text = row["claim_text"].lower()
        if row["judge_ready"] and all(token.lower() in text for token in contains):
            return row
    return None


def evidence_line(prefix: str, row: dict | None, fallback: str = "") -> str | None:
    if not row:
        return fallback or None
    return f"- {prefix}: {row['claim_text'].lstrip('- ').strip()}"


def build_clean_candidate(markdown: str, rows: list[dict], inputs: PipelineInputs) -> str:
    if "monthly_plan_fact_memo" not in inputs.memo_profile:
        return markdown
    lines = [
        "# Evidence-first Ollama memo candidate: memo_02 deep",
        "",
        "## Scope",
    ]
    for prefix, tokens in [
        ("Selected period", ["2026-04"]),
        ("Formula", ["delta", "plan", "fact"]),
        ("Owner route", ["cfo", "owner"]),
        ("Manager mapping", ["manager", "not", "applicable"]),
    ]:
        line = evidence_line(prefix, find_claim(rows, tokens))
        if line:
            lines.append(line)
    lines.extend(
        [
            "",
            "## Evidence-backed package status",
        ]
    )
    for prefix, tokens in [
        ("CFO decomposition", ["cfo", "decomposition"]),
        ("Article hierarchy", ["article", "hierarchy"]),
        ("CFO article localization", ["cfo", "article"]),
        ("Charts", ["charts", "generated"]),
        ("Production readiness", ["production", "readiness"]),
    ]:
        line = evidence_line(prefix, find_claim(rows, tokens))
        if line:
            lines.append(line)
    formula = find_claim(rows, ["delta"]) or find_claim(rows, ["formula"])
    if formula:
        lines.extend(
            [
                "",
                "## Formula semantics",
                "- Delta EUR = Plan EUR - Fact EUR. Positive Delta = fact below plan. Negative Delta = fact above plan. ABS Delta shows scale, not cause.",
            ]
        )
    action = find_claim(rows, ["due", "status"]) or find_claim(rows, ["candidate"])
    lines.extend(["", "## Limitations"])
    if action:
        lines.append(
            "- Статус раздела: реестр кандидатных проверок. Это перечень проверок для валидации владельцами бюджета; он не является финальным планом действий до подтверждения владельца, срока и статуса."
        )
    for prefix, tokens in [
        ("Counterparty", ["counterparty", "causality"]),
        ("Direction", ["direction", "optional"]),
    ]:
        line = evidence_line(prefix, find_claim(rows, tokens))
        if line:
            lines.append(line)
    lines.extend(
        [
            "- Comments are not used as cause evidence in this candidate. Semantic cause analysis is not performed.",
            "",
            "## Evidence Map",
            "",
            "| claim_id | source_file | evidence_level | confidence |",
            "| --- | --- | --- | --- |",
        ]
    )
    for row in rows:
        if row["judge_ready"]:
            lines.append(f"| {row['claim_id']} | {row['source_file']} | {row['evidence_level']} | {row['confidence']} |")
    return "\n".join(lines) + "\n"


def parse_judge_json(text: str) -> dict:
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            try:
                data = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                return {
                    "verdict": "block",
                    "qa_status": "fail",
                    "required_revisions": ["judge returned invalid JSON"],
                    "raw_response": text,
                }
        else:
            return {
                "verdict": "block",
                "qa_status": "fail",
                "required_revisions": ["judge returned invalid JSON"],
                "raw_response": text,
            }
    verdict = str(data.get("verdict", "")).lower()
    if verdict not in {"accept", "revise", "block"}:
        data["verdict"] = "block"
        data.setdefault("required_revisions", []).append("judge verdict missing or invalid")
    data.setdefault("qa_status", "pass" if data.get("verdict") == "accept" else "revise")
    return data


def judge_schema_invalid(data: dict) -> bool:
    revisions = data.get("required_revisions", [])
    return data.get("verdict") == "block" and any(
        item in revisions for item in ["judge returned invalid JSON", "judge verdict missing or invalid"]
    )


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_prompt(name: str) -> str:
    path = PROJECT_ROOT / "prompts" / name
    return read_text_if_exists(path)


def pipeline_paths(inputs: PipelineInputs) -> dict[str, Path]:
    prefix = f"{inputs.memo_profile}__{inputs.depth_mode}"
    return {
        "sanitized_input_package": inputs.output_dir / f"{prefix}__sanitized_input_package.md",
        "sanitization_report": inputs.output_dir / f"{prefix}__sanitization_report.json",
        "judge_narrative_input": inputs.output_dir / f"{prefix}__judge_narrative_input.md",
        "analyst_draft": inputs.output_dir / f"{prefix}__analyst_draft.md",
        "source_registry": inputs.output_dir / f"{prefix}__source_registry.json",
        "claim_evidence_matrix": inputs.output_dir / f"{prefix}__claim_evidence_matrix.json",
        "judge_preflight_report": inputs.output_dir / f"{prefix}__judge_preflight_report.json",
        "evidence_backed_draft": inputs.output_dir / f"{prefix}__evidence_backed_draft.md",
        "judge_json": inputs.output_dir / f"{prefix}__judge_review.json",
        "judge_md": inputs.output_dir / f"{prefix}__judge_review.md",
        "russian_revised": inputs.output_dir / f"{prefix}__russian_revised.md",
        "final_judge_json": inputs.output_dir / f"{prefix}__final_judge_review.json",
        "pipeline_qa": inputs.output_dir / f"{prefix}__pipeline_qa.json",
    }


def accepted_fingerprints(inputs: PipelineInputs) -> dict[str, bytes | None]:
    return {
        "docx": inputs.accepted_final_docx.read_bytes() if inputs.accepted_final_docx and inputs.accepted_final_docx.exists() else None,
        "md": inputs.accepted_final_md.read_bytes() if inputs.accepted_final_md and inputs.accepted_final_md.exists() else None,
    }


def accepted_unchanged(inputs: PipelineInputs, before: dict[str, bytes | None]) -> bool:
    current = accepted_fingerprints(inputs)
    return current == before


def source_registry(inputs: PipelineInputs) -> list[dict]:
    registry = []
    for label, path in [
        ("accepted_package", inputs.accepted_package),
        ("claim_candidates", inputs.claim_candidates),
        ("evidence_map", inputs.evidence_map),
        ("chart_catalog", inputs.chart_catalog),
        ("report_contract", inputs.report_contract),
        ("package_qa", inputs.package_qa),
    ]:
        registry.append(
            {
                "source_id": label,
                "source_file": str(path),
                "exists": path.exists(),
                "char_count": len(read_text_if_exists(path)) if path.exists() else 0,
            }
        )
    return registry


def source_texts(inputs: PipelineInputs) -> list[tuple[str, Path, str]]:
    return [
        (label, path, read_text_if_exists(path))
        for label, path in [
            ("accepted_package", inputs.accepted_package),
            ("claim_candidates", inputs.claim_candidates),
            ("evidence_map", inputs.evidence_map),
            ("chart_catalog", inputs.chart_catalog),
            ("report_contract", inputs.report_contract),
            ("package_qa", inputs.package_qa),
        ]
        if path.exists()
    ]


def evidence_level_for_source(path: str, has_number: bool) -> str:
    lowered = path.lower()
    if not path:
        return "unsupported"
    primary_artifact_tokens = [
        "accepted_package",
        "primary_package",
        "claim_candidates",
        "_claims",
        "evidence_map",
        "claim_audit",
        "chart_catalog",
        "chart_metadata",
        "package_qa",
        "depth_outputs_qa",
        "source_refs",
        "package_manifest",
        "standard_final_manifest",
        "management_depth_manifest",
    ]
    if any(
        token in lowered
        for token in [
            ".csv",
            ".xlsx",
            ".parquet",
            "_qa.json",
        ]
        + primary_artifact_tokens
    ):
        return "primary_metric" if has_number else "primary_table"
    if any(token in lowered for token in ["contract", "readme", "checklist"]):
        return "primary_source_excerpt"
    if any(token in lowered for token in [".md", "memo", "summary", "draft", "conclusion"]):
        return "secondary_narrative"
    return "primary_source_excerpt"


def claim_lines(markdown: str) -> list[tuple[str, str]]:
    section = "body"
    claims = []
    for raw in markdown.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            section = line.strip("# ").strip() or "body"
            continue
        if line.startswith("|") or line.startswith("!") or line == "---":
            continue
        if len(line) < 35:
            continue
        claims.append((section, line))
    return claims


TECHNICAL_MEMO_BODY_SECTION_RE = re.compile(
    r"^\s{0,3}#{1,6}\s*(?:\d+[\.)]\s*)?(?:"
    r"Step-by-Step Guide|Compute Selected Closed Month|Create Excel Workbook|"
    r"Create Excel Workbook Tabs|Generate Charts|Prepare Evidence Map|"
    r"Output Folder Layout|Example Code Snippets|Python Code|Final Steps|"
    r"Review and Validate|Save and Store|QA Check|Package QA|Build Checklist|"
    r"Expected Outputs|Acceptance Criteria|Implementation Steps|Files To Inspect|"
    r"Files Allowed To Modify|Forbidden Actions|Rollback Plan|Tests / Smoke Checks|"
    r"Summary Tab|Top Abs Deviations Tab|Article Month Plan Fact Tab|"
    r"Counterparty Deviations Tab|Fact Without Plan Tab|Plan Without Fact Tab|"
    r"Source Mix Tab|DQ Flags Tab|Evidence Map Tab|QA Summary Tab|"
    r"Top ABS Deviations Chart|Plan and Fact by Article Chart|Plan Fact Gaps Chart|"
    r"Source Mix Limitations Chart"
    r"|Supporting Outputs|Notes|Next Steps|Detailed QA Checks|Final Approval|"
    r"Management-Depth Outputs"
    r")\b",
    flags=re.IGNORECASE,
)


def filter_memo_body(markdown: str) -> str:
    """Remove build/protocol sections if an LLM leaks them into memo body."""
    lines = markdown.splitlines()
    kept: list[str] = []
    skipping_level: int | None = None
    in_code_block = False
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block or is_technical_line(line):
            continue
        heading = re.match(r"^(\s{0,3}#{1,6})\s+", line)
        if heading:
            level = len(heading.group(1).strip())
            if TECHNICAL_MEMO_BODY_SECTION_RE.match(line):
                skipping_level = level
                continue
            if skipping_level is not None and level <= skipping_level:
                skipping_level = None
        if skipping_level is None:
            kept.append(line)
    return "\n".join(kept).strip() + "\n"


def classify_claim(section: str, text: str) -> str:
    lowered = f"{section} {text}".lower()
    if any(token in lowered for token in ["рекоменда", "провер", "action", "действ"]):
        return "recommendation"
    if any(token in lowered for token in ["может", "гипотез", "предварительно"]):
        return "hypothesis"
    if any(token in lowered for token in ["вывод", "показывает", "указывает", "интерпретац"]):
        return "interpretation"
    return "fact"


def source_excerpt_for_claim(claim: str, sources: list[tuple[str, Path, str]]) -> tuple[str, str, str]:
    evidence_ids = re.findall(r"\b(?:EV-[A-Z0-9_-]+|CH_[A-Z0-9_]+)\b", claim)
    if evidence_ids:
        for evidence_id in evidence_ids:
            for _, path, text in sources:
                source_file = str(path)
                if evidence_level_for_source(source_file, bool(re.search(r"\d", claim))) == "secondary_narrative":
                    continue
                lower = text.lower()
                pos = lower.find(evidence_id.lower())
                if pos >= 0:
                    excerpt = text[max(0, pos - 220) : pos + 520].replace("\n", " ").strip()
                    return source_file, excerpt, "strong"
    normalized_claim = re.sub(r"[^A-Za-zА-Яа-я0-9]+", " ", claim).lower()
    tokens = [t for t in normalized_claim.split() if len(t) >= 5][:10]
    best = ("", "", "")
    best_score = 0
    for _, path, text in sources:
        lower = text.lower()
        score = sum(1 for token in tokens if token in lower)
        if score > best_score:
            best_score = score
            first_token = next((token for token in tokens if token in lower), "")
            pos = lower.find(first_token) if first_token else 0
            excerpt = text[max(0, pos - 220) : pos + 420].replace("\n", " ").strip()
            best = (str(path), excerpt, "medium" if score >= 3 else "weak")
    return best if best_score else ("", "", "unsupported")


def build_claim_evidence_matrix(markdown: str, inputs: PipelineInputs) -> tuple[list[dict], dict, str]:
    sources = source_texts(inputs)
    rows = []
    patched_lines = []
    removed_lines = []
    claim_idx = 1
    for raw in markdown.splitlines():
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("|") or stripped.startswith("!") or len(stripped) < 35:
            patched_lines.append(line)
            continue
        section = "body"
        for prev in reversed(patched_lines):
            if prev.strip().startswith("#"):
                section = prev.strip().strip("# ").strip() or "body"
                break
        claim_id = f"C-{claim_idx:03d}"
        claim_idx += 1
        claim_type = classify_claim(section, stripped)
        if any(token in stripped.lower() for token in ["calculation", "расчет", "расчёт", "формула"]):
            claim_type = "calculation"
        source_file, excerpt, confidence = source_excerpt_for_claim(stripped, sources)
        has_number = bool(re.search(r"\d", stripped))
        evidence_level = evidence_level_for_source(source_file, has_number)
        metric_ref = source_file if has_number and evidence_level.startswith("primary_") else ""
        calculation_or_fact = claim_type in {"fact", "calculation"} or has_number
        judge_ready = bool(
            evidence_level != "unsupported"
            and source_file
            and excerpt
            and (not calculation_or_fact or evidence_level.startswith("primary_"))
            and (not has_number or metric_ref)
        )
        fix_action = "keep" if judge_ready else ("downgrade_to_hypothesis" if claim_type in {"interpretation", "recommendation"} else "remove")
        rows.append(
            {
                "claim_id": claim_id,
                "memo_section": section,
                "claim_text": stripped,
                "claim_type": claim_type,
                "source_file": source_file,
                "source_excerpt": excerpt,
                "metric_ref": metric_ref,
                "evidence_level": evidence_level,
                "confidence": confidence,
                "judge_ready": judge_ready,
                "fix_action": fix_action,
            }
        )
        if judge_ready:
            patched_lines.append(f"{line} [EVID: {claim_id}]")
        else:
            removed_lines.append(f"- {claim_id}: {stripped} | fix_action={fix_action}")
    appendix = ["", "## Evidence Map", "", "| claim_id | source_file | confidence |", "| --- | --- | --- |"]
    for row in rows:
        appendix.append(f"| {row['claim_id']} | {row['source_file'] or 'unsupported'} | {row['confidence']} |")
    if removed_lines:
        appendix.extend(["", "## Removed Or Downgraded Claims", ""])
        appendix.extend(removed_lines)
    patched = "\n".join(patched_lines + appendix) + "\n"
    executive_blockers = [
        row
        for row in rows
        if not row["judge_ready"]
        and any(token in row["memo_section"].lower() for token in ["executive", "резюме", "вывод", "recommendation", "рекоменда"])
    ]
    numeric_without_metric = [row for row in rows if re.search(r"\d", row["claim_text"]) and not row["metric_ref"]]
    fact_secondary_only = [
        row
        for row in rows
        if row["claim_type"] in {"fact", "calculation"} and row["evidence_level"] == "secondary_narrative"
    ]
    recommendation_secondary_only = [
        row
        for row in rows
        if row["claim_type"] == "recommendation" and row["evidence_level"] == "secondary_narrative"
    ]
    blockers = executive_blockers + numeric_without_metric + fact_secondary_only + recommendation_secondary_only
    unique_blockers = {row["claim_id"]: row for row in blockers}
    report = {
        "preflight_status": "fail" if unique_blockers else "pass",
        "blocking_claims_count": len(unique_blockers),
        "top_blocking_claims": list(unique_blockers.values())[:10],
        "claims_total": len(rows),
        "claims_judge_ready": sum(1 for row in rows if row["judge_ready"]),
        "claims_with_primary_evidence": sum(1 for row in rows if str(row["evidence_level"]).startswith("primary_")),
        "claims_with_secondary_narrative_only": sum(1 for row in rows if row["evidence_level"] == "secondary_narrative"),
        "unsupported_claims": sum(1 for row in rows if row["evidence_level"] == "unsupported"),
        "claims_with_primary_evidence_rows": [row for row in rows if str(row["evidence_level"]).startswith("primary_")],
        "claims_with_secondary_narrative_support_only": [row for row in rows if row["evidence_level"] == "secondary_narrative"],
        "unsupported_claim_rows": [row for row in rows if row["evidence_level"] == "unsupported"],
        "numeric_claims_without_metric_ref": numeric_without_metric,
        "fact_or_calculation_secondary_only": fact_secondary_only,
        "recommendation_secondary_only": recommendation_secondary_only,
        "removed_or_downgraded_claims": sum(1 for row in rows if row["fix_action"] in {"remove", "downgrade_to_hypothesis"}),
    }
    return rows, report, patched


def run_pipeline(
    inputs: PipelineInputs,
    ollama_client: Callable[[str, str, dict], str] | None = None,
    routing: dict | None = None,
) -> dict:
    routing = routing or load_routing()
    ollama_client = ollama_client or default_ollama_client
    paths = pipeline_paths(inputs)
    inputs.output_dir.mkdir(parents=True, exist_ok=True)
    before = accepted_fingerprints(inputs)
    package, sanitization_report = build_sanitized_input_package(inputs)
    paths["sanitized_input_package"].write_text(package, encoding="utf-8")
    write_json(paths["sanitization_report"], sanitization_report)
    model_trace: list[dict] = []
    allowed_numbers = load_allowed_numbers(
        [
            inputs.accepted_package,
            inputs.claim_candidates,
            inputs.evidence_map,
            inputs.chart_catalog,
            inputs.report_contract,
            inputs.package_qa,
        ]
    )
    qa_context = QaContext(
        allowed_numbers=allowed_numbers,
        due_date_status_confirmed=inputs.due_date_status_confirmed,
        timing_confirmed=inputs.timing_confirmed,
        confirmed_cause_evidence=inputs.confirmed_cause_evidence,
        memo_profile=inputs.memo_profile,
    )

    if not inputs.accepted_final_md or not inputs.accepted_final_md.exists():
        result = {
            "pipeline_status": "blocked_missing_final_narrative",
            "qa_status": "blocked",
            "stage": "narrative_input",
            "error": "accepted_final_md is required for narrative-only judge/preflight input",
            "deterministic_package_valid": True,
            "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
            "model_trace": model_trace,
        }
        write_json(paths["pipeline_qa"], result)
        return result

    judge_narrative = filter_memo_body(read_text_if_exists(inputs.accepted_final_md))
    paths["judge_narrative_input"].write_text(judge_narrative, encoding="utf-8")
    paths["analyst_draft"].write_text(judge_narrative, encoding="utf-8")
    registry = source_registry(inputs)
    matrix, preflight, evidence_backed_draft = build_claim_evidence_matrix(judge_narrative, inputs)
    evidence_backed_draft = build_clean_candidate(evidence_backed_draft, matrix, inputs)
    write_json(paths["source_registry"], {"sources": registry})
    write_json(paths["claim_evidence_matrix"], {"claims": matrix})
    write_json(paths["judge_preflight_report"], preflight)
    paths["evidence_backed_draft"].write_text(evidence_backed_draft, encoding="utf-8")

    text_qa = validate_text(judge_narrative, qa_context)
    if text_qa["qa_status"] != "pass":
        result = {
            "pipeline_status": "block",
            "qa_status": "fail",
            "stage": "text_qa",
            "text_qa": text_qa,
            "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
            "model_trace": model_trace,
        }
        write_json(paths["pipeline_qa"], result)
        return result

    if preflight["preflight_status"] != "pass":
        result = {
            "pipeline_status": "block",
            "qa_status": "blocked",
            "stage": "judge_preflight",
            "judge_preflight_status": "fail",
            "top_blocking_claims": preflight["top_blocking_claims"],
            "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
            "model_trace": model_trace,
        }
        write_json(paths["pipeline_qa"], result)
        return result

    judge_payload = judge_input_package(package, registry, matrix, evidence_backed_draft, preflight)
    try:
        judge_response, judge = call_judge_with_schema(
            judge_prompt_text(read_prompt("ollama_judge_prompt.md"), judge_payload),
            routing,
            ollama_client,
        )
    except Exception as exc:
        result = {
            "pipeline_status": "blocked_ollama_unavailable",
            "qa_status": "blocked",
            "stage": "judge",
            "error": str(exc),
            "deterministic_package_valid": True,
            "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
            "model_trace": model_trace,
        }
        write_json(paths["pipeline_qa"], result)
        return result
    metadata = model_metadata(judge_response)
    if metadata:
        model_trace.append(metadata)

    write_json(paths["judge_json"], judge)
    paths["judge_md"].write_text(
        "\n".join(
            [
                "# Ollama Judge Review",
                "",
                f"verdict: {judge.get('verdict')}",
                f"qa_status: {judge.get('qa_status')}",
                "",
                "## Required revisions",
                *[f"- {item}" for item in judge.get("required_revisions", [])],
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    if judge.get("verdict") == "block":
        result = {
            "pipeline_status": "block",
            "qa_status": "blocked",
            "stage": "judge",
            "judge_verdict": "block",
            "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
            "model_trace": model_trace,
        }
        write_json(paths["pipeline_qa"], result)
        return result
    if judge.get("verdict") == "revise":
        result = {
            "pipeline_status": "revise",
            "qa_status": "revise",
            "stage": "judge",
            "judge_verdict": "revise",
            "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
            "model_trace": model_trace,
        }
        write_json(paths["pipeline_qa"], result)
        return result

    try:
        final_payload = judge_input_package(package, registry, matrix, judge_narrative, preflight)
        final_response, final_judge = call_judge_with_schema(
            judge_prompt_text(read_prompt("ollama_judge_prompt.md"), final_payload),
            routing,
            ollama_client,
        )
    except Exception as exc:
        result = {
            "pipeline_status": "blocked_ollama_unavailable",
            "qa_status": "blocked",
            "stage": "final_judge",
            "error": str(exc),
            "deterministic_package_valid": True,
            "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
            "model_trace": model_trace,
        }
        write_json(paths["pipeline_qa"], result)
        return result
    metadata = model_metadata(final_response)
    if metadata:
        model_trace.append(metadata)
    write_json(paths["final_judge_json"], final_judge)
    status = "accept" if final_judge.get("verdict") == "accept" else str(final_judge.get("verdict", "block"))
    result = {
        "pipeline_status": status,
        "qa_status": "pass" if status == "accept" else status,
        "stage": "complete" if status == "accept" else "final_judge",
        "judge_verdict": judge.get("verdict"),
        "final_judge_verdict": final_judge.get("verdict"),
        "accepted_outputs_unchanged": accepted_unchanged(inputs, before),
        "output_dir": str(inputs.output_dir),
        "model_trace": model_trace,
    }
    write_json(paths["pipeline_qa"], result)
    return result


def main() -> None:
    parser = argparse.ArgumentParser(description="Run Ollama memo narrative pipeline without overwriting accepted outputs.")
    parser.add_argument("--memo-profile", required=True)
    parser.add_argument("--depth-mode", required=True)
    parser.add_argument("--accepted-package", required=True, type=Path)
    parser.add_argument("--claim-candidates", required=True, type=Path)
    parser.add_argument("--evidence-map", required=True, type=Path)
    parser.add_argument("--chart-catalog", required=True, type=Path)
    parser.add_argument("--report-contract", required=True, type=Path)
    parser.add_argument("--package-qa", required=True, type=Path)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_QA_DIR)
    parser.add_argument("--accepted-final-docx", type=Path)
    parser.add_argument("--accepted-final-md", type=Path)
    args = parser.parse_args()
    result = run_pipeline(
        PipelineInputs(
            memo_profile=args.memo_profile,
            depth_mode=args.depth_mode,
            accepted_package=args.accepted_package,
            claim_candidates=args.claim_candidates,
            evidence_map=args.evidence_map,
            chart_catalog=args.chart_catalog,
            report_contract=args.report_contract,
            package_qa=args.package_qa,
            output_dir=args.output_dir,
            accepted_final_docx=args.accepted_final_docx,
            accepted_final_md=args.accepted_final_md,
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))
    raise SystemExit(0 if result.get("qa_status") in {"pass", "revise"} else 1)


if __name__ == "__main__":
    main()
