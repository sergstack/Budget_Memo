# Refactor Risk Register

This register identifies risk groups for future refactor work. It does not approve or implement refactors.

## stage schema / grain

risk: Stage schema or row grain changes silently.

why it matters: `02_stage/01_full_stage.csv` is the source for mart generation and contract tests.

files likely involved: `src/main.py`, `tests/test_output_contract.py`, `SPEC.md`

what must not change silently: columns, grain, date/month handling, source lineage, separators, decimals, encoding.

required approval: explicit Stage contract approval.

required regression check: `stage_contract_validation`.

rollback expectation: revert source change and restore/regenerate local Stage from approved inputs only after authorization.

## mart formulas

risk: formula, threshold, ranking, or signal semantics drift.

why it matters: MART owns metrics, risk basis, rankings, and signal classification.

files likely involved: `src/build_marts.py`, `tests/test_mart_outputs.py`, `SPEC.md`

what must not change silently: plan/fact delta, execution percent, IN denominator rules, YoY/MoM/planning risk formulas, thresholds, QA status.

required approval: explicit business and contract approval.

required regression check: `mart_contract_validation`.

rollback expectation: revert refactor and rebuild local marts only after approval.

## counterparty normalization

risk: counterparty name/key normalization changes matching or lineage.

why it matters: counterparty analysis, concentration, and plan/fact comparisons depend on stable keys.

files likely involved: `src/main.py`, `src/build_marts.py`, `tests/test_output_contract.py`

what must not change silently: missing counterparty handling, key extraction, unknown/p_fact semantics, restored fact keys.

required approval: data contract approval.

required regression check: Stage contract validation plus counterparty mart checks.

rollback expectation: revert normalization change and compare counterparty slices with approved baseline.

## p-fact reconciliation

risk: reconciliation tolerance, adjustment rows, or refund exclusions change.

why it matters: p-fact reconciliation is a financial-control boundary.

files likely involved: `src/main.py`, `tests/test_output_contract.py`, `SPEC.md`

what must not change silently: tolerance, adjustment formula, included_in_reconciliation, refund exclusion behavior.

required approval: financial-control approval.

required regression check: Stage contract validation and reconciliation comparison.

rollback expectation: revert immediately if reconciliation differs without approval.

## IN / OUT / IN-OUT handling

risk: IN denominator or repeated monthly IN-OUT semantics change.

why it matters: proportionality metrics and executive interpretation depend on stable denominator rules.

files likely involved: `src/main.py`, `src/build_marts.py`, `tests/test_output_contract.py`, `tests/test_mart_outputs.py`

what must not change silently: service row semantics, monthly repeated IN-OUT, denominator status, weak base flags.

required approval: formula/output contract approval.

required regression check: Stage and mart contract validation.

rollback expectation: revert and re-run selected local regression before further work.

## source_mix logic

risk: row classification changes materiality, refund, adjustment, or plan/fact interpretation.

why it matters: downstream analysis uses source mix to distinguish plan, fact, refund, and p-fact adjusted rows.

files likely involved: `src/main.py`, `src/build_marts.py`

what must not change silently: `refund_only`, `refund_mixed`, `p_fact_adjusted`, `plan_and_fact`, `plan_only`, `fact_only`.

required approval: Stage contract approval.

required regression check: source_mix baseline comparison.

rollback expectation: revert if any classification changes without approved migration.

## report package generation

risk: generated report packages become incomplete or stale.

why it matters: reports, charts, tables, QA, and manifests are local release artifacts.

files likely involved: `src/build_report.py`, `src/build_depth_mode_outputs.py`, `scripts/verify_accepted_ollama_report_packages.py`

what must not change silently: final paths, manifest semantics, accepted package checks, chart/media references.

required approval: report generation approval.

required regression check: `report_artifact_validation`.

rollback expectation: revert and restore previous accepted local package if needed.

## claim/evidence/LLM boundary

risk: LLM or judge logic invents, weakens, or misclassifies claims.

why it matters: LLM must not calculate, invent numbers, invent causes, or override QA limitations.

files likely involved: `src/run_ollama_memo_pipeline.py`, `scripts/regenerate_memo01_memo02_ollama_factory.py`, `src/qa_ollama_outputs.py`

what must not change silently: allowed numbers, evidence mapping, judge gates, final output blockers, unsupported claim detection.

required approval: LLM/report QA approval.

required regression check: `ollama_live_llm_validation` plus deterministic fixture tests.

rollback expectation: revert generation logic and discard unapproved generated outputs.

## test fixture/data dependency

risk: public CI accidentally starts requiring local corporate data or generated artifacts.

why it matters: GitHub CI must remain public-data-free.

files likely involved: `.github/workflows/repo-smoke.yml`, `tests/`, `scripts/check_test_strategy.py`

what must not change silently: CI command set, test fixture sources, full discovery status.

required approval: CI governance approval.

required regression check: public data-free checks and strategy checker.

rollback expectation: revert CI/test changes that introduce local dependencies.

## artifact leakage

risk: local data, reports, QA artifacts, logs, or generated files are committed.

why it matters: public repository must not expose corporate data or generated confidential artifacts.

files likely involved: `.gitignore`, `scripts/check_repo_public_safety.py`, local ignored folders

what must not change silently: ignored folder coverage, forbidden extension coverage, tracked file safety checks.

required approval: security/repo hygiene approval.

required regression check: `scripts/check_repo_public_safety.py`.

rollback expectation: remove from index without deleting local files; rotate secrets and perform approved history cleanup if exposure was committed.
