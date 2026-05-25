# First Commit Candidate Review

Status: pass for first-commit candidate review before staging.

No files were staged, committed, or pushed during this review.

## Summary

- Original candidate count before this review artifact: 147 files.
- Candidate source command: `git ls-files --others --exclude-standard`.
- Dry-run source command: `git add --dry-run .`.
- Candidate-only secret scan result: no matches.
- Recommendation: ready to stage reviewed safe files, subject to human review of document contents.

## Grouped Candidate Files

### Repo Setup (5)

- `.env.example`
- `.gitattributes`
- `.gitignore`
- `AGENTS.md`
- `requirements.txt`

### Documentation (63)

- `99_docs/MEMO_FACTORY_DEFAULT_STANDARD.md`
- `99_docs/MEMO_FACTORY_KNOWN_REGRESSIONS.md`
- `99_docs/MEMO_FACTORY_RUNBOOK.md`
- `99_docs/MEMO_PACKAGE_ACCEPTANCE_CHECKLIST.md`
- `99_docs/MODEL_ROUTING_MAX_CHAIN_DOCTRINE.md`
- `99_docs/PROJECT_INSTRUCTIONS.md`
- `99_docs/README.md`
- `99_docs/golden_memo_pack/GOLDEN_MEMO_PACK_STANDARD.md`
- `99_docs/golden_memo_pack/HANDOFF_TO_CODEX.md`
- `99_docs/golden_memo_pack/MANIFEST.md`
- `99_docs/golden_memo_pack/README.md`
- `99_docs/golden_memo_pack/acceptance_checklist.md`
- `99_docs/golden_memo_pack/bad_cases.contract.yml`
- `99_docs/golden_memo_pack/claim_freeze_rules.yml`
- `99_docs/golden_memo_pack/golden_case.contract.yml`
- `99_docs/golden_memo_pack/judge_rubric.draft.yml`
- `99_docs/golden_memo_pack/memo_template.md`
- `99_docs/knowledge/ANALYTICS_MAIN_FILES_STANDARD.md`
- `99_docs/knowledge/ANALYTICS_QA_ACCEPTANCE.md`
- `99_docs/knowledge/ANALYTICS_ROUTING_RULES.md`
- `99_docs/qa/SMOKE_QA_RESULT.md`
- `Codex_Tasks/Memo_Build/00_MASTER_MEMO_ROADMAP.md`
- `Codex_Tasks/Memo_Build/00_TEMPLATE_MEMO_PROFILE_TASK.md`
- `Codex_Tasks/Memo_Build/01_MEMO_01_DEPTH_CLEANUP.md`
- `Codex_Tasks/Memo_Build/02_MONTHLY_PLAN_FACT_MEMO.md`
- `Codex_Tasks/Memo_Build/03_PLANNING_RISK_MEMO.md`
- `Codex_Tasks/Memo_Build/04_WEEKLY_COO_CASH_COST_MEMO.md`
- `Codex_Tasks/Memo_Build/05_DATA_QUALITY_BLOCKER_MEMO.md`
- `Codex_Tasks/Memo_Build/06_IN_OUT_PRESSURE_MEMO.md`
- `Codex_Tasks/Memo_Build/07_ARTICLE_DEEP_DIVE_MEMO.md`
- `Codex_Tasks/Memo_Build/08_CFO_OWNER_LOCALIZATION_MEMO.md`
- `Codex_Tasks/Memo_Build/09_COUNTERPARTY_QUALITY_MEMO.md`
- `Codex_Tasks/Memo_Build/10_QUARTERLY_BUDGET_DYNAMICS_REVIEW.md`
- `Codex_Tasks/Memo_Build/11_SOURCE_MIX_RECONCILIATION_MEMO.md`
- `Codex_Tasks/Memo_Build/12_CURRENCY_LEGAL_ENTITY_MEMO.md`
- `Codex_Tasks/Memo_Build/13_TIMING_CANDIDATES_MEMO.md`
- `Codex_Tasks/Memo_Build/14_REFUND_IMPACT_MEMO.md`
- `Codex_Tasks/Memo_Build/15_COUNTERPARTY_CONCENTRATION_MEMO.md`
- `Codex_Tasks/Memo_Build/16_FORECAST_RUN_RATE_MEMO.md`
- `Codex_Tasks/Memo_Build/17_BUDGET_OWNER_ACTION_REGISTER_MEMO.md`
- `Codex_Tasks/Memo_Build/18_BOARD_LEVEL_BUDGET_SUMMARY.md`
- `PROJECT_ARCHITECTURE_SUMMARY.md`
- `PROJECT_ARTIFACT_INVENTORY.md`
- `PROJECT_DECISIONS_AND_LESSONS.md`
- `PROJECT_DEPTH_MODES.md`
- `PROJECT_HANDOFF_NEXT_CHAT.md`
- `PROJECT_INSTRUCTIONS.md`
- `PROJECT_MEMO_REGISTRY.md`
- `PROJECT_NEXT_MEMOS_PLAN.md`
- `PROJECT_STATUS.md`
- `README.md`
- `SPEC.md`
- `TESTING.md`
- `docs/ANALYTICAL_MEMO_VISUAL_STANDARD.md`
- `docs/DOCX_VISUAL_QA_GATE.md`
- `docs/github_publication_checklist.md`
- `golden_memo_pack/GOLDEN_MEMO_PACK_STANDARD.md`
- `golden_memo_pack/HANDOFF_TO_CODEX.md`
- `golden_memo_pack/MANIFEST.md`
- `golden_memo_pack/README.md`
- `golden_memo_pack/acceptance_checklist.md`
- `golden_memo_pack/memo_template.md`
- `tasks.md`

### Source Code (25)

- `src/build_chart_package.py`
- `src/build_controlled_draft_memo.py`
- `src/build_deep_conclusion_layer.py`
- `src/build_depth_mode_outputs.py`
- `src/build_docx_report.py`
- `src/build_draft_data_package.py`
- `src/build_executive_slice_workbook.py`
- `src/build_marts.py`
- `src/build_memo02_management_depth.py`
- `src/build_memo02_standard_final.py`
- `src/build_memo_draft.py`
- `src/build_memo_profiles.py`
- `src/build_memo_revised.py`
- `src/build_report.py`
- `src/build_report_contract.py`
- `src/export_docx_final_md.py`
- `src/llm_revise_memo_narratives.py`
- `src/main.py`
- `src/ollama_routing.py`
- `src/polish_docx_report.py`
- `src/progress.py`
- `src/qa_ollama_outputs.py`
- `src/rebuild_memo01_depth_package.py`
- `src/regenerate_clean_memo_narratives.py`
- `src/run_ollama_memo_pipeline.py`

### Scripts (10)

- `scripts/check_claim_freeze_diff.py`
- `scripts/check_no_release_on_fail.py`
- `scripts/diagnose_docx_visual_quality.py`
- `scripts/regenerate_memo01_memo02_ollama_factory.py`
- `scripts/validate_golden_memo_pack.py`
- `scripts/validate_release_manifest.py`
- `scripts/verify_accepted_ollama_report_packages.py`
- `scripts/verify_claim_freeze_for_release.py`
- `scripts/verify_high_risk_release_readiness.py`
- `scripts/verify_memo_factory_quality_gates.py`

### Tests (22)

- `tests/fixtures/golden_memo_pack/frozen_claim_registry.json`
- `tests/fixtures/golden_memo_pack/revised_claims.json`
- `tests/fixtures/memo_factory_doctrine/high_risk_missing_human_review.json`
- `tests/fixtures/memo_factory_doctrine/human_acceptance_note.md`
- `tests/fixtures/memo_factory_doctrine/judge_report.json`
- `tests/fixtures/memo_factory_doctrine/quality_gates_missing_stop_rule.yml`
- `tests/fixtures/memo_factory_doctrine/release_manifest_missing_required.json`
- `tests/fixtures/memo_factory_doctrine/release_manifest_valid.json`
- `tests/fixtures/memo_factory_doctrine/render_qa.json`
- `tests/fixtures/ollama_bad_action_final_without_due.md`
- `tests/fixtures/ollama_bad_english_terms.md`
- `tests/fixtures/ollama_bad_invented_number.md`
- `tests/fixtures/ollama_bad_planning_risk_as_fact.md`
- `tests/fixtures/ollama_bad_unsupported_cause.md`
- `tests/fixtures/ollama_good_output.md`
- `tests/test_docx_visual_quality_contract.py`
- `tests/test_golden_memo_pack_contract.py`
- `tests/test_mart_outputs.py`
- `tests/test_memo_factory_doctrine_enforcement.py`
- `tests/test_ollama_memo_pipeline.py`
- `tests/test_ollama_memo_pipeline_integration.py`
- `tests/test_output_contract.py`

### Prompts (3)

- `prompts/ollama_analyst_prompt.md`
- `prompts/ollama_judge_prompt.md`
- `prompts/ollama_russian_revisor_prompt.md`

### Schemas And Contracts (11)

- `00_contracts/direction_manager_mapping_contract.md`
- `00_contracts/mart_contract.md`
- `00_contracts/metrics_contract.md`
- `00_contracts/stage_contract.md`
- `golden_memo_pack/bad_cases.contract.yml`
- `golden_memo_pack/claim_freeze_rules.yml`
- `golden_memo_pack/golden_case.contract.yml`
- `golden_memo_pack/judge_rubric.draft.yml`
- `schemas/judge_report.schema.json`
- `schemas/memo_factory_quality_gate_result.schema.json`
- `schemas/release_manifest.schema.json`

### Config Examples (4)

- `config/docx_style_contract.yml`
- `config/memo_factory_quality_gates.yml`
- `config/memo_factory_routing_config.json`
- `config/ollama_memo_routing.json`

### Launch Commands (4)

- `run_all_reports_ollama_factory_check.command`
- `run_depth_outputs.command`
- `run_memo01_memo02_ollama_factory_generation.command`
- `run_pipeline.command`

### Questionable / Needs Review (0)

No candidate files require exclusion based on filename, type, ignore behavior, or candidate-only secret scan.

## Risky Filename Matches

The risky-pattern command matched 26 candidate filenames. All are classified as `safe_code_or_doc` because they are source code, documentation, schemas, tests, or placeholder templates, not generated data files or credential files.

| File | Classification | Reason |
| --- | --- | --- |
| `.env.example` | safe_code_or_doc | Placeholder environment template, not a real env file. |
| `00_contracts/mart_contract.md` | safe_code_or_doc | Contract documentation. |
| `00_contracts/stage_contract.md` | safe_code_or_doc | Contract documentation. |
| `99_docs/knowledge/ANALYTICS_QA_ACCEPTANCE.md` | safe_code_or_doc | QA process documentation. |
| `99_docs/qa/SMOKE_QA_RESULT.md` | safe_code_or_doc | QA documentation. |
| `Codex_Tasks/Memo_Build/05_DATA_QUALITY_BLOCKER_MEMO.md` | safe_code_or_doc | Task documentation. |
| `PROJECT_ARTIFACT_INVENTORY.md` | safe_code_or_doc | Project documentation. |
| `docs/DOCX_VISUAL_QA_GATE.md` | safe_code_or_doc | QA documentation. |
| `run_all_reports_ollama_factory_check.command` | safe_code_or_doc | Launch command script. |
| `run_depth_outputs.command` | safe_code_or_doc | Launch command script. |
| `schemas/judge_report.schema.json` | safe_code_or_doc | Schema file. |
| `scripts/verify_accepted_ollama_report_packages.py` | safe_code_or_doc | Verification script. |
| `src/build_depth_mode_outputs.py` | safe_code_or_doc | Source code. |
| `src/build_docx_report.py` | safe_code_or_doc | Source code. |
| `src/build_draft_data_package.py` | safe_code_or_doc | Source code. |
| `src/build_marts.py` | safe_code_or_doc | Source code. |
| `src/build_report.py` | safe_code_or_doc | Source code. |
| `src/build_report_contract.py` | safe_code_or_doc | Source code. |
| `src/export_docx_final_md.py` | safe_code_or_doc | Source code. |
| `src/polish_docx_report.py` | safe_code_or_doc | Source code. |
| `src/qa_ollama_outputs.py` | safe_code_or_doc | Source code. |
| `tests/fixtures/memo_factory_doctrine/judge_report.json` | safe_code_or_doc | Test fixture. |
| `tests/fixtures/memo_factory_doctrine/render_qa.json` | safe_code_or_doc | Test fixture. |
| `tests/fixtures/ollama_good_output.md` | safe_code_or_doc | Test fixture. |
| `tests/test_mart_outputs.py` | safe_code_or_doc | Test code. |
| `tests/test_output_contract.py` | safe_code_or_doc | Test code. |

## Not Recommended For First Commit

No files from the 147 visible candidates are excluded by this review.

The following local paths remain not recommended and should stay ignored:

- `01_raw/`
- `02_stage/`
- `03_marts/`
- `04_charts/`
- `04_signals/`
- `05_evidence/`
- `05_llm_package/`
- `06_reports/`
- `07_qa/`
- `99_archive/`
- `artifacts/`
- `src/06_reports/`
- binary workbooks, CSV/TSV, Parquet, SQLite/database files, archives, logs, caches, and local OS/editor artifacts

## Blockers

None.

## Assumptions

- Documentation files do not contain confidential business values beyond project/process descriptions.
- Test fixtures are synthetic or safe examples.
- Config JSON/YAML files are routing and quality-gate configuration, not private credentials.

## Risks And Limitations

- This review checks filenames, Git visibility, ignore behavior, and secret-pattern matches. It does not replace a human line-by-line confidentiality review of every document.
- Future generated artifacts can become visible if placed outside ignored paths or with new file extensions.
