from __future__ import annotations

import unittest

from scripts.check_test_strategy import (
    check_required_files,
    check_text_markers,
    check_workflow,
    workflow_disallowed_markers,
    workflow_missing_required_markers,
)


class TestStrategyCheckTest(unittest.TestCase):
    def test_required_strategy_files_exist(self) -> None:
        self.assertEqual(check_required_files(), [])

    def test_required_text_markers_exist(self) -> None:
        self.assertEqual(check_text_markers(), {})

    def test_repo_smoke_workflow_is_data_free(self) -> None:
        workflow = check_workflow()
        self.assertEqual(workflow["disallowed"], [])
        self.assertEqual(workflow["missing_required"], [])

    def test_workflow_marker_helpers_detect_unsafe_commands(self) -> None:
        unsafe = "python src/main.py\npython -m unittest discover -s tests -q\n"
        self.assertIn("src/main.py", workflow_disallowed_markers(unsafe))
        self.assertIn("python -m unittest discover", workflow_disallowed_markers(unsafe))

    def test_workflow_marker_helpers_detect_missing_commands(self) -> None:
        self.assertTrue(workflow_missing_required_markers(""))


if __name__ == "__main__":
    unittest.main()
