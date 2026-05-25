# Repo Hardening Audit

## Summary

Status: `safe_to_fix_now` for repository hygiene additions only.

This audit covers the public repository structure after the safe baseline push. No business logic, formulas, schemas, output contracts, raw data, stage outputs, mart outputs, report artifacts, or QA artifacts were changed.

## Repo State

Classification: `safe_to_fix_now`

- Branch at audit start: `main`.
- Safe baseline observed: `12ec18b chore: create safe repository baseline`.
- Working tree was clean before the hardening branch was created.
- Hardening branch: `chore/repo-hardening-v1`.
- Remote: `origin https://github.com/sergstack/Budget_Memo.git`.

## Branch Audit

Classification: `safe_to_fix_now`

- Local branches observed: `main`, then `chore/repo-hardening-v1`.
- Remote branch observed: `origin/main`.
- No branches were deleted.
- No force push was used.

## Canonical Structure Audit

Classification: `needs_manual_review`

The repository has a public-safe tracked layer for code, docs, tests, configs, schemas, contracts, prompts, and run launchers. Data and generated layers are ignored/local.

Canonical public structure now includes:

- repo setup: `.gitignore`, `.gitattributes`, `.env.example`, `requirements.txt`
- docs: `README.md`, `TESTING.md`, `PROJECT_*.md`, `99_docs/`, `docs/`
- contracts/schemas: `00_contracts/`, `schemas/`
- source/scripts: `src/`, `scripts/`
- tests: `tests/`
- prompts/config: `prompts/`, `config/`
- public smoke CI: `.github/workflows/repo-smoke.yml`

Residual structure risks:

- Documentation is intentionally rich but duplicated across root `PROJECT_*.md`, `99_docs/`, `golden_memo_pack/`, and `Codex_Tasks/`.
- Some tests are public-safe while others are local data-dependent; CI must stay explicit.

## Tracked File Safety Audit

Classification: `safe_to_fix_now`

Tracked-file safety scan found no forbidden tracked data-layer paths or forbidden data/binary output extensions.

Allowed filename terms include `stage`, `mart`, `report`, `qa`, `artifact`, `token`, and `data` when used in source code, docs, tests, schemas, prompts, or safe config files.

Keyword scan matches are treated as `needs_manual_review` only when they could contain real credentials. Current matches are placeholder ignore rules, config token-count fields, command variables, documentation, and source-code terminology.

## Ignored Data/Artifact Layer Audit

Classification: `safe_to_fix_now`

The following layers are ignored/local and must remain out of Git:

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
- outputs, logs, temp folders, caches, and binary data formats

## Test Strategy Audit

Classification: `safe_to_fix_now`

Public data-free checks:

- `python scripts/check_repo_public_safety.py`
- `python -m unittest tests.test_repo_public_safety -q`
- `python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml`

Local data-dependent checks:

- full unit discovery
- stage contract tests
- mart output tests
- accepted-package verification
- report generation and render QA

Ollama-dependent checks require explicit approval and a reachable local model endpoint.

## CI Readiness Audit

Classification: `safe_to_fix_now`

The safe CI path must not run the full pipeline, full test discovery, report generation, DOCX/PDF rendering, Ollama, or LibreOffice-dependent commands.

The repo-smoke workflow runs only data-free repository safety and quality-gate config checks.

## Performance Backlog

Classification: `needs_manual_review`

- import-time filesystem scanning: `low_risk_future_optimization`
- repeated Excel reading/cleaning: `medium_risk_requires_contract_tests`
- DataFrame `.apply(axis=1)`: `medium_risk_requires_contract_tests`
- repeated DOCX/PDF/chart generation: `medium_risk_requires_contract_tests`
- hardcoded large mappings: `high_risk_business_logic_sensitive`
- lack of data-free tests: `safe_to_fix_now`
- CI unsuitability of full tests: `safe_to_fix_now`
- scripts that write to ignored output folders during import or tests: `do_not_change` until isolated by tests

No performance optimization is implemented in this task.

## Business-Logic Sensitive Files

Classification: `do_not_touch_without_approval`

- `src/main.py`
- `src/build_marts.py`
- `src/build_depth_mode_outputs.py`
- `src/run_ollama_memo_pipeline.py`
- `src/ollama_routing.py`
- `src/llm_revise_memo_narratives.py`
- `src/regenerate_clean_memo_narratives.py`
- `scripts/regenerate_memo01_memo02_ollama_factory.py`
- `schemas/`
- `00_contracts/`
- `config/memo_factory_quality_gates.yml`
- `config/memo_factory_routing_config.json`
- `config/ollama_memo_routing.json`
- `prompts/`
- data-dependent contract tests

## Safe-To-Change Files

Classification: `safe_to_fix_now`

For repo hygiene tasks only:

- `README.md`
- `TESTING.md`
- `docs/repo_hardening_audit.md`
- `docs/repo_cleanup_policy.md`
- `docs/public_clone_smoke_check.md`
- `scripts/check_repo_public_safety.py`
- `tests/test_repo_public_safety.py`
- `.github/workflows/repo-smoke.yml`

## Do-Not-Touch Files And Folders

Classification: `do_not_touch_without_approval`

- raw, stage, mart, chart, signal, evidence, LLM package, report, QA, archive, and artifact folders
- formulas, schemas, output contracts, financial-control logic, row grain, and column names
- final memo outputs and accepted QA/release artifacts

## Recommended Next Tasks

- `safe_to_fix_now`: keep CI limited to public data-free checks.
- `safe_to_fix_now`: review docs for external confidentiality before broader public sharing.
- `needs_manual_review`: classify which existing tests are data-free vs data-dependent.
- `needs_manual_review`: create a future performance SPEC before optimizing Excel reads, `.apply(axis=1)`, chart generation, or DOCX rendering.
- `do_not_touch_without_approval`: do not refactor stage/mart/report pipelines without contract tests and explicit approval.
- `blocked`: full public CI for the whole pipeline is blocked by intentionally ignored corporate data and generated artifacts.
