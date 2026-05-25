# Budget Plan-Fact Final Export

Clean ETL project for final user-facing budget exports.

## Public Repository Scope

This public repository intentionally excludes corporate source data and generated artifacts. Local data and outputs remain ignored under folders such as `01_raw/`, `02_stage/`, `03_marts/`, `04_charts/`, `04_signals/`, `05_evidence/`, `05_llm_package/`, `06_reports/`, `07_qa/`, `99_archive/`, and `artifacts/`.

Public clones can run only data-free smoke checks:

```bash
python scripts/check_repo_public_safety.py
python -m unittest tests.test_repo_public_safety -q
python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

Full pipeline execution and full regression tests require local ignored corporate data and generated artifacts. Do not run the full pipeline, report generation, or Ollama/live LLM generation from a public clone.

## For Reviewers / Contributors

- [Reviewer quickstart](docs/reviewer_quickstart.md)
- [Contributing guide](CONTRIBUTING.md)
- [Testing guide](TESTING.md)
- [Repository governance](docs/repo_governance.md)
- [Documentation map](docs/documentation_map.md)

## Current Project State

First analytical memo pilot is completed and frozen for handoff:

- accepted memo profile: `executive_yoy_mom_budget_memo`;
- active report folder: `06_reports/01_executive_yoy_mom_budget_memo/`;
- accepted standard memo: `06_reports/01_executive_yoy_mom_budget_memo/final/01_executive_yoy_mom_budget_memo__standard__2026-05-21__final.docx`;
- production readiness is not claimed.

Start here for the next chat:

- [PROJECT_HANDOFF_NEXT_CHAT.md](PROJECT_HANDOFF_NEXT_CHAT.md)
- [PROJECT_STATUS.md](PROJECT_STATUS.md)
- [PROJECT_MEMO_REGISTRY.md](PROJECT_MEMO_REGISTRY.md)
- [PROJECT_NEXT_MEMOS_PLAN.md](PROJECT_NEXT_MEMOS_PLAN.md)
- [PROJECT_DEPTH_MODES.md](PROJECT_DEPTH_MODES.md)
- [PROJECT_ARTIFACT_INVENTORY.md](PROJECT_ARTIFACT_INVENTORY.md)

## Inputs

- `01_raw/budget_rows/raw_YYYY-MM.xlsx`
- `01_raw/dds/dds_YYYY-MM.xlsx`
- `01_raw/p-fact/p-fact_YYYY-MM.xlsx`
- `01_raw/dds article/dds_article.xlsx`

Raw files are read only. Some workbooks contain XLSX sheet attributes unsupported by the installed reader, so the pipeline reads temporary cleaned copies and does not alter `01_raw/`.

## Output

The pipeline writes one user-facing skeleton stage CSV:

- `02_stage/01_full_stage.csv`

This file is the project `stage_main_full` analogue and the source for mart generation. In this project, base skeleton financial measures `План, EUR`, `Факт, EUR`, and `IN-OUT, EUR` are allowed in Stage; derived metrics, risk labels, materiality flags, management conclusions, and recommendations are not.

`source_row_id` may contain grouped lineage after aggregation, with multiple raw row ids separated by ` | `. `load_timestamp` / `pipeline_run_id` and a dedicated rejected-rows artifact are not currently part of the Stage output; adding them requires separate approval and must be backward-compatible.

Audit CSVs are written to:

- `02_stage/audit/`

The file uses `;` as separator, `,` as decimal marker, and UTF-8 BOM encoding.

## Run

Build the stage layer:

```bash
python3 src/main.py
```

Expected stdout includes:

```text
reconciliation_failed_pairs=0
total_reconciliation_pairs=<int>
max_abs_plan_diff=<number>
max_abs_fact_diff=<number>
```

Build the production mart, signal, evidence, report, and QA layers:

```bash
python3 src/build_marts.py
```

Generate accepted memo depth outputs for memo 01:

```bash
python3 src/build_depth_mode_outputs.py
```

Current memo 01 outputs are written to:

```text
06_reports/01_executive_yoy_mom_budget_memo/
```

On macOS, double-click:

```text
run_pipeline.command
```

It runs both `src/main.py` and `src/build_marts.py`.

For memo depth outputs only, double-click:

```text
run_depth_outputs.command
```

Run the Ollama memo factory generator:

```bash
python3 scripts/regenerate_memo01_memo02_ollama_factory.py --memo memo02 --depth standard
```

Supported generator options, verified with `--help`:

```text
--dry-run
--memo {memo01,memo02,01_executive_yoy_mom_budget_memo,02_monthly_plan_fact_memo}
--start-depth {short,standard,deep,action}
--depth {short,standard,deep,action}
```

Before launching generation from scripts, check for an active run without matching the check command itself:

```bash
pgrep -af "[s]cripts/regenerate_memo01_memo02_ollama_factory.py"
```

Layer outputs:

- `03_marts/`: production Parquet marts only
- `04_signals/`: signal tables
- `05_evidence/`: evidence cards and LLM context package
- `06_reports/`: Excel and memo/report artifacts
- `07_qa/`: deterministic QA files

## Test

```bash
python3 -m unittest discover -s tests -q
```
