from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from src.qa_ollama_outputs import QaContext, validate_text


ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "fixtures"


class OllamaMemoPipelineQaTests(unittest.TestCase):
    def setUp(self) -> None:
        self.allowed_numbers = {
            "10.47 млн",
            "10.56 млн",
            "-92.6 тыс",
            "2026",
            "04",
        }
        self.context = QaContext(allowed_numbers=self.allowed_numbers, memo_profile="monthly_plan_fact_memo")

    def validate_fixture(self, name: str) -> dict:
        text = (FIXTURES / name).read_text(encoding="utf-8")
        return validate_text(text, self.context)

    def test_good_output_passes(self) -> None:
        result = self.validate_fixture("ollama_good_output.md")
        self.assertEqual(result["qa_status"], "pass", result)
        self.assertEqual(result["recommendation"], "accept")

    def test_invented_number_fails_numeric_guard(self) -> None:
        result = self.validate_fixture("ollama_bad_invented_number.md")
        self.assertEqual(result["qa_status"], "fail")
        self.assertIn("777 млн", result["new_numeric_claims"])

    def test_unsupported_cause_fails_causality_guard(self) -> None:
        result = self.validate_fixture("ollama_bad_unsupported_cause.md")
        self.assertEqual(result["qa_status"], "fail")
        self.assertTrue(result["causality_violations"])

    def test_final_action_without_due_fails_action_guard(self) -> None:
        result = self.validate_fixture("ollama_bad_action_final_without_due.md")
        self.assertEqual(result["qa_status"], "fail")
        self.assertTrue(result["action_maturity_violations"])

    def test_english_terms_fail_language_guard(self) -> None:
        result = self.validate_fixture("ollama_bad_english_terms.md")
        self.assertEqual(result["qa_status"], "fail")
        self.assertIn("accepted package", result["language_violations"])
        self.assertIn("source mix", result["language_violations"])
        self.assertIn("cfo x article", result["language_violations"])

    def test_planning_risk_as_fact_fails_guard(self) -> None:
        result = self.validate_fixture("ollama_bad_planning_risk_as_fact.md")
        self.assertEqual(result["qa_status"], "fail")
        self.assertTrue(result["planning_risk_violations"])

    def test_judge_revise_blocks_final_gate(self) -> None:
        text = (FIXTURES / "ollama_good_output.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            judge_path = Path(tmp) / "judge.json"
            judge_path.write_text(json.dumps({"verdict": "revise"}), encoding="utf-8")
            result = validate_text(text, self.context, judge_path)
        self.assertEqual(result["qa_status"], "fail")
        self.assertEqual(result["judge_verdict_gate"], "fail")
        self.assertIn("judge_verdict=revise", result["judge_verdict_issues"])

    def test_judge_accept_allows_final_gate(self) -> None:
        text = (FIXTURES / "ollama_good_output.md").read_text(encoding="utf-8")
        with tempfile.TemporaryDirectory() as tmp:
            judge_path = Path(tmp) / "judge.json"
            judge_path.write_text(json.dumps({"verdict": "accept"}), encoding="utf-8")
            result = validate_text(text, self.context, judge_path)
        self.assertEqual(result["qa_status"], "pass", result)
        self.assertEqual(result["judge_verdict_gate"], "pass")


if __name__ == "__main__":
    unittest.main()
