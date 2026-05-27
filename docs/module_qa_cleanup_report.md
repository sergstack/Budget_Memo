# Module QA Cleanup Report

## Summary

Full local validation was run on a local checkout with ignored corporate data and generated artifacts available. Safe public checks passed with `python3`; exact `python ...` commands failed because `python` is not installed in this shell.

No business logic, formulas, schemas, output contracts, metrics, column names, QA gates, release checks, or generated artifacts were changed for commit. Cleanup is limited to documenting the module map and updating `TESTING.md` with the required `src/build_memo_profiles.py` prerequisite for full local test discovery after a fresh mart rebuild.

## Module map

| Module | Path | Status | Check used | Result | Action |
|---|---|---|---|---|---|
| repo_public_safety | `scripts/check_repo_public_safety.py`, `tests/test_repo_public_safety.py`, `.github/workflows/repo-smoke.yml` | working | public safety script and unittest | pass | keep |
| test_strategy_policy | `scripts/check_test_strategy.py`, `tests/test_test_strategy.py`, `docs/test_strategy_matrix.md`, `docs/ci_matrix.md` | working | script and unittest | pass | keep |
| etl_stage | `src/main.py`, `01_raw/`, `02_stage/` | working_with_data_required | `python3 src/main.py` | pass; rows=42217; reconciliation_failed_pairs=0 | keep |
| mart_generation | `src/build_marts.py`, `03_marts/`, `04_signals/`, `05_evidence/` | working_with_data_required | `python3 src/build_marts.py` | pass; qa_status=pass; raw_untouched=True; stage_untouched=True | keep |
| memo_profile_catalog | `src/build_memo_profiles.py`, `03_marts/memo_profile_*`, `07_qa/memo_profile_catalog_qa_report.json` | working_with_data_required | `python3 src/build_memo_profiles.py` | pass; 18 profiles; 4 depth modes | keep; documented prerequisite |
| depth_outputs | `src/build_depth_mode_outputs.py`, `06_reports/01_executive_yoy_mom_budget_memo/` | working_with_data_required | `python3 src/build_depth_mode_outputs.py` | pass | keep |
| signals | `04_signals/`, `src/build_marts.py`, `src/build_memo_profiles.py` | working_with_data_required | mart/profile builds and full unittest | pass | keep |
| evidence | `05_evidence/`, `src/build_marts.py` | working_with_data_required | mart build and full unittest | pass | keep |
| llm_package | `05_llm_package/`, `src/build_draft_data_package.py`, prompts | working_with_data_required | memo factory dry-run/full run | pass for memo01/memo02 standard | keep |
| memo_generation | `src/build_*memo*.py`, `src/build_report*.py`, `src/memo_renderer.py` | working_with_data_required | full unittest and generated memo factory outputs | pass where exercised; remaining report modules are artifact-dependent | keep |
| memo_factory_ollama | `scripts/regenerate_memo01_memo02_ollama_factory.py`, `src/run_ollama_memo_pipeline.py`, `src/ollama_routing.py` | working_with_data_required | help, dry-run, full memo01/memo02 standard runs | pass; final_judge=accept for both | keep |
| qa_validation | `scripts/verify_memo_factory_quality_gates.py`, `scripts/verify_accepted_ollama_report_packages.py`, `scripts/validate_golden_memo_pack.py`, `scripts/check_no_release_on_fail.py` | working | quality gates, accepted package verification, golden pack validation | pass with required args; no-arg package commands show expected usage errors | keep |
| render_docx_pdf | LibreOffice render path inside memo factory, `scripts/diagnose_docx_visual_quality.py` | working_with_data_required | memo factory render checks and full unittest coverage | pass for memo01/memo02 standard | keep |
| chart_media_checks | `src/build_chart_package.py`, `04_charts/`, memo factory media checks | working_with_data_required | memo factory media/chart checks | pass; memo01 media=10, memo02 media=11 | keep |
| release_verification | release manifest, publication, promotion scripts and tests | safe_smoke_only | full unittest and accepted package verification | pass in test/smoke scope; no production publish run | keep |
| run_commands | `run_pipeline.command`, `run_depth_outputs.command`, `run_all_reports_ollama_factory_check.command`, `run_memo01_memo02_ollama_factory_generation.command` | safe_smoke_only | reference inspection only | referenced by docs or names match active commands | keep |
| tests | `tests/` | working | `python3 -m unittest discover -s tests -q` | pass; 75 tests, 5 skipped | keep |
| docs | `README.md`, `TESTING.md`, `CONTRIBUTING.md`, `docs/`, `PROJECT_*.md`, `99_docs/` | working | inspection and doc consistency update | pass | keep |
| generated_or_ignored | `01_raw/`, `02_stage/`, `03_marts/`, `04_charts/`, `04_signals/`, `05_evidence/`, `05_llm_package/`, `06_reports/`, `07_qa/`, `99_archive/`, `artifacts/` | do_not_touch | ignored status and local validation output inventory | not staged; not committed | do not commit |
| legacy_or_unknown | `99_docs/`, `Codex_Tasks/`, historical archive folders | do_not_touch | reference inspection only | preserved as historical/backlog context | keep; needs separate approval before deletion |

## Script and source classification

| Path | Status | Check used | Action |
|---|---|---|---|
| `src/main.py` | working_with_data_required | stage build | keep |
| `src/build_marts.py` | working_with_data_required | mart build and tests | keep |
| `src/build_memo_profiles.py` | working_with_data_required | direct run and tests | keep |
| `src/build_depth_mode_outputs.py` | working_with_data_required | direct run and tests | keep |
| `src/build_chart_package.py` | working_with_data_required | full unittest and memo factory checks | keep |
| `src/build_draft_data_package.py` | working_with_data_required | memo factory path | keep |
| `src/build_report_contract.py` | working_with_data_required | tests/import coverage | keep |
| `src/build_docx_report.py` | working_with_data_required | tests/import coverage and render path | keep |
| `src/build_report.py` | working_with_data_required | tests/import coverage | keep |
| `src/memo_renderer.py` | working | full unittest | keep |
| `src/memo_display_contract.py` | working | full unittest | keep |
| `src/memo_release_manifest.py` | working | full unittest | keep |
| `src/qa_ollama_outputs.py` | working | full unittest and memo factory text QA | keep |
| `src/run_ollama_memo_pipeline.py` | working | full unittest and memo factory validation | keep |
| `src/ollama_routing.py` | working | full unittest and memo factory routing output | keep |
| `src/progress.py` | working | progress output during generators | keep |
| `src/llm_revise_memo_narratives.py` | working | full unittest coverage of revisor safety | keep |
| `src/build_memo_draft.py`, `src/build_memo_revised.py`, `src/build_controlled_draft_memo.py`, `src/build_deep_conclusion_layer.py`, `src/rebuild_memo01_depth_package.py`, `src/regenerate_clean_memo_narratives.py`, `src/polish_docx_report.py`, `src/export_docx_final_md.py`, `src/build_executive_slice_workbook.py`, `src/build_memo02_management_depth.py`, `src/build_memo02_standard_final.py` | working_with_data_required | import/reference/full-suite coverage where applicable | keep; no cleanup without separate report-artifact scope |
| `scripts/check_repo_public_safety.py` | working | direct run and unittest | keep |
| `scripts/check_test_strategy.py` | working | direct run and unittest | keep |
| `scripts/verify_memo_factory_quality_gates.py` | working | direct run | keep |
| `scripts/regenerate_memo01_memo02_ollama_factory.py` | working_with_data_required | help, dry-run, full memo01/memo02 standard generation | keep |
| `scripts/verify_accepted_ollama_report_packages.py` | working_with_data_required | run with `--output-dir` | keep; docs still contain a no-arg example |
| `scripts/validate_golden_memo_pack.py` | working | run with `--pack` and `--out` | keep |
| `scripts/check_no_release_on_fail.py`, `scripts/check_claim_freeze_diff.py`, `scripts/verify_claim_freeze_for_release.py`, `scripts/validate_release_manifest.py`, `scripts/verify_high_risk_release_readiness.py` | working | full unittest or helper invocation coverage | keep |
| `scripts/diagnose_docx_visual_quality.py` | working_with_data_required | full unittest help/contract coverage | keep |
| `scripts/run_synthetic_memo_release_pilot.py`, `scripts/run_monthly_plan_fact_standard_draft_release_pilot.py`, `scripts/run_memo02_standard_draft_release_flow.py`, `scripts/run_memo02_standard_analytical_draft_release_flow.py`, `scripts/promote_memo02_standard_draft_release.py`, `scripts/publish_memo02_standard_final_release.py` | safe_smoke_only | full unittest coverage for flow/promotion/publication contracts | keep |

## Safe public checks run

- `git status --short --branch`: clean before edits on `chore/module-qa-full-local-cleanup`.
- `git diff --stat`: empty before edits.
- `git diff --check`: pass before edits.
- `python scripts/check_repo_public_safety.py`: failed, `python` command not found.
- `python -m unittest tests.test_repo_public_safety -q`: failed, `python` command not found.
- `python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml`: failed, `python` command not found.
- `python3 scripts/check_repo_public_safety.py`: pass.
- `python3 -m unittest tests.test_repo_public_safety -q`: pass; 5 tests.
- `python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml`: pass.
- `python3 scripts/check_test_strategy.py`: pass.
- `python3 -m unittest tests.test_test_strategy -q`: pass; 7 tests.

## Full local checks run

- `python3 src/main.py`: pass; wrote `02_stage/01_full_stage.csv`; rows=42217; reconciliation_failed_pairs=0.
- `python3 src/build_marts.py`: pass; qa_status=pass; raw_untouched=True; stage_untouched=True.
- `python3 src/build_depth_mode_outputs.py`: pass.
- `python3 -m unittest discover -s tests -q`: first run failed because `07_qa/memo_profile_catalog_qa_report.json` was missing after fresh mart rebuild.
- `python3 src/build_memo_profiles.py`: pass; profile QA pass; depth modes QA pass; 18 profiles; 4 depth modes.
- `python3 -m unittest discover -s tests -q`: pass; 75 tests; 5 skipped.
- `python3 scripts/regenerate_memo01_memo02_ollama_factory.py --help`: pass.
- `pgrep -af "[s]cripts/regenerate_memo01_memo02_ollama_factory.py" || true`: no persistent active generator before full generation.
- `python3 scripts/regenerate_memo01_memo02_ollama_factory.py --dry-run --memo memo01 --depth standard`: pass.
- `python3 scripts/regenerate_memo01_memo02_ollama_factory.py --dry-run --memo memo02 --depth standard`: pass.
- `python3 scripts/regenerate_memo01_memo02_ollama_factory.py --memo memo01 --depth standard`: pass; text_qa=pass; preflight=pass; final_judge=accept; media=10.
- `python3 scripts/regenerate_memo01_memo02_ollama_factory.py --memo memo02 --depth standard`: pass; text_qa=pass; preflight=pass; final_judge=accept; media=11.
- `python3 scripts/verify_accepted_ollama_report_packages.py`: failed with usage error because `--output-dir` is required.
- `python3 scripts/verify_accepted_ollama_report_packages.py --output-dir artifacts/module_qa/accepted_package_verification_20260527_1011`: pass; 8/8 records.
- `python3 scripts/validate_golden_memo_pack.py`: failed with usage error because `--pack` and `--out` are required.
- `python3 scripts/validate_golden_memo_pack.py --pack golden_memo_pack --out artifacts/module_qa/golden_memo_pack_validation_20260527_1011`: pass; positive case blocked_expected as designed.

## Working modules

- Public repository safety, CI smoke policy, and test strategy checks.
- Stage ETL against local ignored corporate data.
- Mart/signal/evidence generation.
- Memo profile/depth catalog generation.
- Memo01 and memo02 standard Ollama factory generation in the local environment.
- DOCX build, media checks, LibreOffice render checks, chart manifest checks, and final judge chain for memo01/memo02 standard.
- Full unittest suite after profile/depth QA artifacts are generated.
- Accepted package verification with required `--output-dir`.
- Golden Memo Pack offline validation with required `--pack` and `--out`.

## Modules requiring local data/artifacts

- `src/main.py`, `src/build_marts.py`, `src/build_memo_profiles.py`, `src/build_depth_mode_outputs.py`.
- Report, DOCX, render, chart media, accepted package, and memo factory paths under `06_reports/`, `07_qa/`, and `artifacts/`.
- `scripts/regenerate_memo01_memo02_ollama_factory.py` requires local LLM/Ollama availability for full generation.
- Full test discovery requires local ignored generated artifacts and the profile/depth QA step after fresh mart rebuild.

## Broken or suspicious modules

- `TESTING.md` documented full unittest discovery but did not document the `src/build_memo_profiles.py` prerequisite after fresh mart rebuild. This caused the first full unittest run to fail on missing `07_qa/memo_profile_catalog_qa_report.json`.
- `TESTING.md` and some docs still show `python3 scripts/verify_accepted_ollama_report_packages.py` without the now-required `--output-dir`; the command itself is working when called with `--output-dir`.
- `scripts/validate_golden_memo_pack.py` is working, but no-arg invocation is not meaningful because `--pack` and `--out` are required.
- Several active release/promotion scripts have low textual reference counts outside tests; they are covered by unit tests and are not safe deletion candidates.

## Cleanup performed

- Added this module QA cleanup report.
- Updated `TESTING.md` to document `python3 src/build_memo_profiles.py` as a required local step before full test discovery after a fresh mart rebuild.
- No source code, tests, business logic, formulas, schemas, output contracts, generated reports, data, or artifacts were changed for commit.
- No files were deleted.

## Cleanup candidates not touched

- Local ignored `.DS_Store`, `.pytest_cache`, and `__pycache__` files are safe local garbage, but they are ignored and not part of the PR; they were not deleted to avoid broad local filesystem churn.
- Historical docs under `99_docs/` and task backlog files under `Codex_Tasks/` overlap with current docs but are preserved as historical/backlog context.
- Release/promotion scripts with low reference counts are preserved because tests cover them and deletion could weaken release controls.
- Generated/local artifacts under ignored layers are not staged or committed.
- No-arg docs for `scripts/verify_accepted_ollama_report_packages.py` should be corrected in a focused follow-up if maintainers want docs to require `--output-dir` everywhere.

## Risks

- Full local validation used ignored corporate data and generated local artifacts.
- Memo factory full generation used local LLM/Ollama and regenerated ignored report/QA artifacts.
- The command `pgrep -af "[s]cripts/regenerate_memo01_memo02_ollama_factory.py" || true && python3 ...` printed a transient shell PID before memo02 generation; a separate follow-up `pgrep` pattern should be run alone when checking active generators.
- `python` is unavailable in this shell; `python3` is the meaningful local interpreter.
- The generated artifact timestamp inventory was produced from file mtimes after validation because the initial GNU `find -printf` snapshot command is unsupported on this macOS shell.

## Follow-up PRs

- Update docs that show `scripts/verify_accepted_ollama_report_packages.py` without `--output-dir`.
- Add a small orchestrator or documented command sequence for full local validation: Stage -> marts -> memo profiles -> depth outputs -> tests.
- Add a public-safe checker warning when docs list `python` commands in environments that standardize on `python3`.
- Consider a separate local-only cleanup task for ignored `.DS_Store`, `.pytest_cache`, and `__pycache__` files if maintainers want workspace hygiene beyond PR contents.
