from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

import src.run_ollama_memo_pipeline as pipeline
from src.run_ollama_memo_pipeline import PipelineInputs, call_judge_with_schema, evidence_level_for_source, filter_memo_body, judge_input_package, run_pipeline, sanitize_llm_input_text


GOOD_DRAFT = """# Memo

## Резюме
- [DATA FACT] План 10,47 млн EUR; факт 10,56 млн EUR; Delta -92,6 тыс. EUR. Источник: пакет.

График: Источник: принятый пакет. Метрика: ABS Delta EUR. Период: 2026-04. Ограничение: масштаб, не причина.

## Плановый риск
- [LIMITATION] Плановый риск является будущим бюджетным риском; это не факт исполнения. Источник: evidence.

## Действия
- [RECOMMENDATION] Кандидат проверки: маршрут проверки = ЦФО; требует подтверждения срока и статуса. Источник: action QA.

## Ограничения
- [LIMITATION] Комментарии руководителей отсутствуют, поэтому семантический анализ причин не выполнялся. Источник: QA.
- [LIMITATION] Direction является optional analytical grouping и не блокирует выпуск. Источник: mapping QA.
- [LIMITATION] Действия остаются кандидатами до подтверждения срока и статуса. Источник: action QA.
- [LIMITATION] Delta EUR = Plan EUR - Fact EUR. Положительная Delta = факт ниже плана. Отрицательная Delta = факт выше плана. ABS Delta показывает масштаб, не причину. Источник: formula.
"""

BAD_NUMBER = GOOD_DRAFT.replace("## Ограничения", "- [DATA FACT] Новый эффект 777 млн EUR. Источник: пакет.\n\n## Ограничения")
BAD_ENGLISH = GOOD_DRAFT.replace("Кандидат проверки", "accepted package source mix final action plan")


class MockOllama:
    def __init__(self, responses: dict[str, list[str] | str], fail_role: str | None = None):
        self.responses = {role: list(value) if isinstance(value, list) else [value] for role, value in responses.items()}
        self.fail_role = fail_role
        self.calls: list[str] = []
        self.prompts: list[str] = []

    def __call__(self, role: str, prompt: str, routing: dict) -> str:
        self.calls.append(role)
        self.prompts.append(prompt)
        if self.fail_role == role:
            raise RuntimeError("mocked ollama unavailable")
        values = self.responses.get(role)
        if not values:
            raise AssertionError(f"Unexpected role call: {role}")
        return values.pop(0)


class OllamaMemoPipelineIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.base = Path(self.tmp.name)
        self.package = self.write("accepted_package.md", "10,47 млн EUR\n10,56 млн EUR\n-92,6 тыс. EUR\n2026-04\n")
        self.claims = self.write("claim_candidates.md", "10,47 млн EUR\n10,56 млн EUR\n-92,6 тыс. EUR\n")
        self.evidence = self.write("evidence_map.md", "EV-PLANFACT-001\n")
        self.charts = self.write("chart_catalog.md", "График: Источник: пакет. Метрика: ABS Delta EUR. Период: 2026-04. Ограничение: масштаб.\n")
        self.contract = self.write("contract.md", "Delta EUR = Plan EUR - Fact EUR\n")
        self.package_qa = self.write("package_qa.md", "qa_status: pass\n")
        self.accepted_docx = self.write("accepted.docx", "accepted docx bytes")
        self.accepted_md_text = GOOD_DRAFT
        self.accepted_md = self.write("accepted.md", self.accepted_md_text)
        self.output_dir = self.base / "07_qa" / "llm_narrative_qa"
        self.routing = {"roles": []}

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def write(self, name: str, text: str) -> Path:
        path = self.base / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def inputs(self) -> PipelineInputs:
        return PipelineInputs(
            memo_profile="monthly_plan_fact_memo",
            depth_mode="depth_2_management_memo",
            accepted_package=self.package,
            claim_candidates=self.claims,
            evidence_map=self.evidence,
            chart_catalog=self.charts,
            report_contract=self.contract,
            package_qa=self.package_qa,
            output_dir=self.output_dir,
            accepted_final_docx=self.accepted_docx,
            accepted_final_md=self.accepted_md,
        )

    def assert_accepted_unchanged(self) -> None:
        self.assertEqual(self.accepted_docx.read_text(encoding="utf-8"), "accepted docx bytes")
        self.assertEqual(self.accepted_md.read_text(encoding="utf-8"), self.accepted_md_text)

    def test_happy_path_writes_review_outputs_only(self) -> None:
        mock = MockOllama(
            {
                "analyst": GOOD_DRAFT,
                "judge": [
                    json.dumps({"verdict": "accept", "qa_status": "pass"}),
                    json.dumps({"verdict": "accept", "qa_status": "pass"}),
                ],
                "russian_revisor": GOOD_DRAFT,
            }
        )
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "accept", result)
        self.assertEqual(result["qa_status"], "pass")
        self.assertTrue(result["accepted_outputs_unchanged"])
        self.assert_accepted_unchanged()
        self.assertTrue((self.output_dir / "monthly_plan_fact_memo__depth_2_management_memo__analyst_draft.md").exists())
        preflight = json.loads((self.output_dir / "monthly_plan_fact_memo__depth_2_management_memo__judge_preflight_report.json").read_text(encoding="utf-8"))
        self.assertEqual(preflight["preflight_status"], "pass")
        self.assertIn("claims_with_primary_evidence_rows", preflight)
        self.assertIn("claims_with_secondary_narrative_support_only", preflight)
        self.assertIn("numeric_claims_without_metric_ref", preflight)
        self.assertFalse((self.base / "final.docx").exists())

    def test_primary_package_and_claims_are_primary_evidence(self) -> None:
        self.assertEqual(
            evidence_level_for_source("07_qa/inputs/monthly_plan_fact_memo__standard__primary_package.md", has_number=True),
            "primary_metric",
        )
        self.assertEqual(
            evidence_level_for_source("07_qa/inputs/m2_short_claims.md", has_number=False),
            "primary_table",
        )

    def test_final_judge_payload_includes_preflight_summary(self) -> None:
        matrix = [
            {
                "claim_id": "C-001",
                "claim_text": "Источник: проверенный факт.",
                "evidence_level": "primary_table",
                "judge_ready": True,
            }
        ]
        preflight = {
            "preflight_status": "pass",
            "blocking_claims_count": 0,
            "claims_total": 1,
            "claims_judge_ready": 1,
            "claims_with_primary_evidence": 1,
            "claims_with_secondary_narrative_only": 0,
            "unsupported_claims": 0,
            "top_blocking_claims": [],
        }
        payload = judge_input_package("package", [], matrix, "draft", preflight)
        self.assertIn("# Deterministic preflight summary", payload)
        self.assertIn('"preflight_status": "pass"', payload)
        self.assertIn('"blocking_claims_count": 0', payload)
        self.assertIn('"claims_with_primary_evidence": 1', payload)
        self.assertIn('"claims_with_secondary_narrative_only": 0', payload)

    def test_judge_revise_blocks_final_generation(self) -> None:
        mock = MockOllama({"analyst": GOOD_DRAFT, "judge": json.dumps({"verdict": "revise", "qa_status": "revise", "required_revisions": ["soften wording"]})})
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "revise", result)
        self.assertEqual(mock.calls, ["judge"])
        self.assert_accepted_unchanged()

    def test_valid_unfavorable_judge_verdict_does_not_use_fallback(self) -> None:
        mock = MockOllama({"judge": json.dumps({"verdict": "revise", "qa_status": "revise", "required_revisions": ["evidence issue"]})})
        _, parsed = call_judge_with_schema("prompt", self.routing, mock)
        self.assertEqual(parsed["verdict"], "revise")
        self.assertFalse(parsed["fallback_used"])
        self.assertEqual(parsed["fallback_reason"], "")
        self.assertEqual(mock.calls, ["judge"])

    def test_invalid_schema_with_custom_client_is_not_silently_accepted(self) -> None:
        mock = MockOllama({"judge": "not json"})
        _, parsed = call_judge_with_schema("prompt", self.routing, mock)
        self.assertEqual(parsed["verdict"], "block")
        self.assertEqual(parsed["schema_status"], "invalid")
        self.assertFalse(parsed["fallback_used"])
        self.assertEqual(parsed["fallback_reason"], "mock_or_custom_client_no_fallback")

    def test_filter_removes_build_sections_from_candidate_body(self) -> None:
        text = """# Memo

## Executive Summary
Keep this management section.

## Output Folder Layout
06_reports/02_monthly_plan_fact_memo/

## Package QA
- Missing direction and confirmed manager blockers are present.

## Limitations
Keep this limitation section.
"""
        filtered = filter_memo_body(text)
        self.assertIn("Keep this management section.", filtered)
        self.assertIn("Keep this limitation section.", filtered)
        self.assertNotIn("Output Folder Layout", filtered)
        self.assertNotIn("Package QA", filtered)
        self.assertNotIn("06_reports/02_monthly_plan_fact_memo", filtered)

    def test_sanitized_input_package_excludes_code_paths_and_folder_layout(self) -> None:
        dirty = """# Memo source
Management claim: План 10,47 млн EUR and fact 10,56 млн EUR need review.
![Chart](06_reports/02_monthly_plan_fact_memo/charts/x.png)

## Output Folder Layout
- `03_marts/mart_main_full_budget.parquet`

## Example Code Snippets
```python
import pandas as pd
df.sort_values("abs_delta_eur").head(10)
```

## Evidence
EV-PLANFACT-001 supports management interpretation.
"""
        sanitized, removed = sanitize_llm_input_text(dirty)
        self.assertIn("Management claim", sanitized)
        self.assertIn("EV-PLANFACT-001", sanitized)
        self.assertNotIn("03_marts", sanitized)
        self.assertNotIn(".sort_values", sanitized)
        self.assertNotIn(".head(", sanitized)
        self.assertNotIn("Output Folder Layout", sanitized)
        self.assertGreaterEqual(len(removed), 5)

    def test_pipeline_writes_and_uses_sanitized_input_package(self) -> None:
        self.package.write_text(
            "Management claim: План 10,47 млн EUR and fact 10,56 млн EUR need review.\n"
            "## Output Folder Layout\n"
            "- `03_marts/mart_main_full_budget.parquet`\n"
            "```python\n"
            "df.sort_values('abs_delta_eur').head(10)\n"
            "```\n",
            encoding="utf-8",
        )
        mock = MockOllama(
            {
                "analyst": GOOD_DRAFT,
                "judge": [
                    json.dumps({"verdict": "accept", "qa_status": "pass"}),
                    json.dumps({"verdict": "accept", "qa_status": "pass"}),
                ],
                "russian_revisor": GOOD_DRAFT,
            }
        )
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "accept", result)
        sanitized_path = self.output_dir / "monthly_plan_fact_memo__depth_2_management_memo__sanitized_input_package.md"
        sanitized = sanitized_path.read_text(encoding="utf-8")
        self.assertIn("Management claim", sanitized)
        self.assertNotIn("03_marts", sanitized)
        self.assertNotIn(".sort_values", sanitized)
        self.assertNotIn(".head(", sanitized)
        narrative_path = self.output_dir / "monthly_plan_fact_memo__depth_2_management_memo__judge_narrative_input.md"
        narrative = narrative_path.read_text(encoding="utf-8")
        self.assertNotIn("Output Folder Layout", narrative)
        self.assertNotIn("03_marts", narrative)

    def test_judge_block_stops_pipeline(self) -> None:
        mock = MockOllama({"analyst": GOOD_DRAFT, "judge": json.dumps({"verdict": "block", "qa_status": "fail"})})
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "block", result)
        self.assertEqual(result["stage"], "judge")
        self.assertEqual(mock.calls, ["judge"])
        self.assertFalse((self.output_dir / "monthly_plan_fact_memo__depth_2_management_memo__russian_revised.md").exists())
        self.assert_accepted_unchanged()

    def test_revisor_bad_number_is_blocked_by_text_qa(self) -> None:
        self.accepted_md_text = BAD_NUMBER
        self.accepted_md.write_text(self.accepted_md_text, encoding="utf-8")
        mock = MockOllama({"analyst": GOOD_DRAFT, "judge": json.dumps({"verdict": "accept", "qa_status": "pass"}), "russian_revisor": BAD_NUMBER})
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "block", result)
        self.assertEqual(result["stage"], "text_qa")
        self.assertIn("777 млн", result["text_qa"]["new_numeric_claims"])
        self.assert_accepted_unchanged()

    def test_revisor_anglicisms_are_blocked_by_text_qa(self) -> None:
        self.accepted_md_text = BAD_ENGLISH
        self.accepted_md.write_text(self.accepted_md_text, encoding="utf-8")
        mock = MockOllama({"analyst": GOOD_DRAFT, "judge": json.dumps({"verdict": "accept", "qa_status": "pass"}), "russian_revisor": BAD_ENGLISH})
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "block", result)
        self.assertIn("accepted package", result["text_qa"]["language_violations"])
        self.assertIn("source mix", result["text_qa"]["language_violations"])
        self.assertIn("final action plan", result["text_qa"]["language_violations"])
        self.assert_accepted_unchanged()

    def test_ollama_unavailable_blocks_narrative_only(self) -> None:
        mock = MockOllama({}, fail_role="judge")
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "blocked_ollama_unavailable", result)
        self.assertTrue(result["deterministic_package_valid"])
        self.assert_accepted_unchanged()

    def test_default_client_records_primary_fallback_metadata(self) -> None:
        calls = []

        def fake_call(url, model, prompt, options, timeout=300, response_format=None):
            calls.append(model)
            if len(calls) == 1:
                raise pipeline.OllamaUnavailable("primary down")
            return "fallback response"

        original = pipeline.call_ollama
        pipeline.call_ollama = fake_call
        try:
            response = pipeline.default_ollama_client(
                "analyst",
                "prompt",
                {
                    "ollama_url": "http://127.0.0.1:11434",
                    "roles": [
                        {
                            "role": "analyst",
                            "primary_model": "primary-model",
                            "fallback_model": "fallback-model",
                        }
                    ],
                },
            )
        finally:
            pipeline.call_ollama = original

        self.assertEqual(str(response), "fallback response")
        self.assertEqual(calls, ["primary-model", "fallback-model"])
        self.assertTrue(response.metadata["fallback_used"])
        self.assertEqual(response.metadata["primary_model"], "primary-model")
        self.assertEqual(response.metadata["fallback_model"], "fallback-model")
        self.assertEqual(response.metadata["final_model"], "fallback-model")

    def test_no_overwrite_guard_with_existing_accepted_outputs(self) -> None:
        mock = MockOllama(
            {
                "analyst": GOOD_DRAFT,
                "judge": [
                    json.dumps({"verdict": "accept", "qa_status": "pass"}),
                    json.dumps({"verdict": "accept", "qa_status": "pass"}),
                ],
                "russian_revisor": GOOD_DRAFT,
            }
        )
        before_docx = self.accepted_docx.read_bytes()
        before_md = self.accepted_md.read_bytes()
        result = run_pipeline(self.inputs(), mock, self.routing)
        self.assertEqual(result["pipeline_status"], "accept")
        self.assertEqual(self.accepted_docx.read_bytes(), before_docx)
        self.assertEqual(self.accepted_md.read_bytes(), before_md)
        for path in self.output_dir.iterdir():
            self.assertTrue(path.is_file())
            self.assertTrue(str(path).startswith(str(self.output_dir)))


if __name__ == "__main__":
    unittest.main()
