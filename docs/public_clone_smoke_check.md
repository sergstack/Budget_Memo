# Public Clone Smoke Check

This repository is published without corporate source data and without generated analytical artifacts.

## Data-Free Checks

Run these checks after cloning the public repository:

```bash
python scripts/check_repo_public_safety.py
python -m unittest tests.test_repo_public_safety -q
python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

These checks inspect tracked files, required repository metadata, `.gitignore` safety coverage, and memo factory quality-gate configuration. They do not require raw workbooks, stage CSVs, mart Parquet files, report folders, Ollama, or LibreOffice.

## Local Data-Dependent Checks

These commands require ignored local corporate data or generated artifacts and are not suitable for a public clone:

```bash
python3 src/main.py
python3 src/build_marts.py
python3 -m unittest discover -s tests -q
```

Stage contract tests, mart output tests, accepted-package checks, report generation, DOCX rendering, and full memo factory checks depend on local layers such as `01_raw/`, `02_stage/`, `03_marts/`, `04_charts/`, `05_evidence/`, `06_reports/`, and `07_qa/`.

## Ollama And Report Generation

Do not run Ollama/live LLM generation, report regeneration, DOCX/PDF rendering, or full pipeline commands from a public clone unless local data and model/runtime prerequisites are explicitly available and the task authorizes that execution.
