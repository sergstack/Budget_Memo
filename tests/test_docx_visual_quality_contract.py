from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]


class DocxVisualQualityContractTests(unittest.TestCase):
    def test_style_contract_yaml_exists_and_has_required_sections(self) -> None:
        path = ROOT / "config" / "docx_style_contract.yml"
        self.assertTrue(path.exists())
        payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        for section in [
            "page",
            "fonts",
            "tables",
            "charts",
            "language",
            "appendix",
            "publishing_hygiene",
        ]:
            self.assertIn(section, payload)

    def test_diagnostic_script_exists_and_has_cli_help(self) -> None:
        script = ROOT / "scripts" / "diagnose_docx_visual_quality.py"
        self.assertTrue(script.exists())
        result = subprocess.run(
            [sys.executable, str(script), "--help"],
            cwd=ROOT,
            check=False,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--docx", result.stdout)
        self.assertIn("--out", result.stdout)
        self.assertRegex(result.stdout, r"Does not run live\s+Kestra")

    def test_docs_exist_and_define_verdicts_and_severity(self) -> None:
        docs = [
            ROOT / "docs" / "ANALYTICAL_MEMO_VISUAL_STANDARD.md",
            ROOT / "docs" / "DOCX_VISUAL_QA_GATE.md",
        ]
        for path in docs:
            self.assertTrue(path.exists(), path)
            text = path.read_text(encoding="utf-8")
            for verdict in [
                "docx_render_status",
                "visual_layout_status",
                "executive_readability_status",
                "publishing_hygiene_status",
                "overall_visual_release_status",
            ]:
                self.assertIn(verdict, text)
            self.assertIn("Severity Matrix", text)
            self.assertRegex(text.lower(), r"business logic")
            self.assertRegex(text.lower(), r"must not|prohibit")


if __name__ == "__main__":
    unittest.main()
