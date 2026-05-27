# AGENTS.md

## Project purpose

Budget_Memo is a budget plan-fact / analytical memo automation repository.

It contains deterministic ETL, mart generation, evidence packages, memo/report artifacts, and QA/release checks.

Corporate source data and generated artifacts are intentionally excluded from the public repository.

## Operating mode

Default cycle:

```text
Inspect → Plan → Implement → Test → Review → Report
```

Long-run mode:

- continue on safe, local, reversible assumptions;
- stop only on hard blockers;
- keep changes minimal and scoped;
- preserve Budget_Memo guardrails;
- run the smallest meaningful checks;
- log assumptions in the final report.

## Hard blockers

Stop and report blocker when:

- secrets, `.env`, credentials, or tokens are needed;
- production/runtime/deploy/migration is involved;
- business logic, formulas, metric definitions, schemas, APIs, output contracts, or column names may change;
- raw/stage/mart/report artifacts must be modified without explicit task approval;
- full pipeline, memo regeneration, or Ollama/live LLM generation is needed but not explicitly allowed;
- destructive file operations are required;
- no meaningful validation is possible;
- acceptance criteria conflict.

## Project Rules

- Keep changes minimal, factual, and reproducible.
- Use Python for all numeric calculations, aggregations, percentages, reconciliation checks, and financial logic.
- Treat raw inputs under `01_raw/` as read-only unless a task explicitly allows raw input changes.
- Do not modify `02_stage/` or `03_marts/` unless the task explicitly allows stage or mart work.
- Do not change formulas, schemas, or financial-control logic without explicit approval.
- Do not run Ollama generation, memo regeneration, or live report pipelines unless the task explicitly asks for it.
- Do not delete validation, QA, release, or audit artifacts.
- Report verification commands and results factually.

## Project Layers

```text
RAW → STAGE → MARTS → ANALYSIS → LLM PACKAGE → REPORT → QA → ARCHIVE
```

- `01_raw/`: source input workbooks.
- `02_stage/`: cleaned stage outputs and stage audit files.
- `03_marts/`: accepted mart and slice outputs.
- `04_charts/` and `04_signals/`: chart data and analytical signals.
- `05_evidence/` and `05_llm_package/`: evidence and LLM context packages.
- `06_reports/`: report packages, final memo outputs, charts, tables, source refs, and package QA.
- `07_qa/`: timestamped cross-package QA artifacts.
- `99_archive/`: archived or superseded artifacts.

## Testing expectations

Safe public smoke checks:

```bash
python scripts/check_repo_public_safety.py
python -m unittest tests.test_repo_public_safety -q
python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

General test command when local test data and artifacts are available:

```bash
python3 -m unittest discover -s tests -q
```

Local/full commands require explicit task approval and local ignored corporate data or generated artifacts:

```bash
python3 src/main.py
python3 src/build_marts.py
python3 scripts/verify_accepted_ollama_report_packages.py
```

Do not run full pipeline, report generation, memo regeneration, or Ollama/live LLM generation unless explicitly requested.

## Guardrails

- Do not rebuild marts during report-only tasks.
- Do not modify final memo outputs under `06_reports/*/final/` unless the task explicitly requests regeneration or final artifact updates.
- Do not weaken `text_qa`, `judge_preflight`, final judge, render QA, chart/media checks, or release verification.
- Do not invent numbers, owners, due dates, statuses, timing claims, or business causes.
- Use accepted marts, slices, logic workbooks, claim registries, evidence cards, and chart manifests as report source of truth.

## Final report format

```text
Summary:
Files changed:
Tests/checks run:
Assumptions:
Risks/limitations:
Rollback:
Acceptance status:
Next step:
```
