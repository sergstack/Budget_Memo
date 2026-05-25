from __future__ import annotations

import unittest

from scripts.check_repo_public_safety import (
    REQUIRED_GOVERNANCE_FILES,
    check_gitignore_patterns,
    check_required_files,
    is_forbidden_tracked_file,
    run_git_ls_files,
)


class RepoPublicSafetyTest(unittest.TestCase):
    def test_no_forbidden_tracked_public_files(self) -> None:
        tracked = run_git_ls_files()
        forbidden = [path for path in tracked if is_forbidden_tracked_file(path)]
        self.assertEqual(forbidden, [])

    def test_required_public_repo_files_exist(self) -> None:
        self.assertEqual(check_required_files(), [])

    def test_required_governance_files_exist(self) -> None:
        missing = set(check_required_files())
        self.assertTrue(REQUIRED_GOVERNANCE_FILES)
        for path in REQUIRED_GOVERNANCE_FILES:
            self.assertNotIn(path, missing)

    def test_required_gitignore_safety_patterns_exist(self) -> None:
        self.assertEqual(check_gitignore_patterns(), [])

    def test_env_example_allowed_but_real_env_forbidden(self) -> None:
        self.assertFalse(is_forbidden_tracked_file(".env.example"))
        self.assertTrue(is_forbidden_tracked_file(".env"))
        self.assertTrue(is_forbidden_tracked_file("01_raw/raw.xlsx"))
        self.assertTrue(is_forbidden_tracked_file("06_reports/final.docx"))


if __name__ == "__main__":
    unittest.main()
