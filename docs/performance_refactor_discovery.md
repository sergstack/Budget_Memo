# Performance And Refactor Discovery

Stage 6 is discovery-only. No code was changed, no optimization was implemented, no full pipeline was run, no report generation was run, and no Ollama/live LLM was run.

## Summary

The project has several expected performance hotspots for a data/report pipeline: repeated Excel reads and XLSX cleaning, large pandas `groupby`/`merge`/`concat` paths, row-wise DataFrame operations, DOCX/PDF/render work, and Ollama/live LLM calls. These are plausible bottlenecks based on static inspection only; they require local regression gates before implementation.

## Scope Inspected

- `src/`
- `scripts/`
- `tests/`
- root repository docs and governance files
- test strategy, CI, local regression, artifact, and performance/refactor gate docs

## Entrypoints Inspected

- `src/main.py`
- `src/build_marts.py`
- `src/build_report.py`
- `src/build_depth_mode_outputs.py`
- `src/run_ollama_memo_pipeline.py`
- `scripts/regenerate_memo01_memo02_ollama_factory.py`
- `scripts/verify_accepted_ollama_report_packages.py`
- `scripts/diagnose_docx_visual_quality.py`
- data-dependent tests under `tests/`

## Pipeline I/O Findings

| Finding | Classification | Evidence | Future gate |
| --- | --- | --- | --- |
| XLSX cleaning copies workbook XML before reading source files. | `medium_risk_pipeline_io` | `src/main.py` has `clean_xlsx_for_reader()` and `read_xlsx()`. | Stage contract validation and raw/stage artifact comparison. |
| DDS workbook is read twice in `build_dds()`. | `medium_risk_pipeline_io` | `src/main.py` has two consecutive `read_xlsx(source_path, tmp_path)` calls. | Stage contract validation before any fix. |
| Mart rebuild cleans output folders before rebuilding. | `high_risk_business_logic_sensitive` | `src/build_marts.py` uses `clean_rebuild_dirs()`. | Local regression plan and artifact leakage check. |
| Report and package scripts scan output trees and artifact directories. | `medium_risk_report_artifact` | `rglob()`/`glob()` patterns appear in report, package, and QA scripts. | Artifact validation matrix and report artifact validation. |

## Pandas / Dataframe Findings

| Finding | Classification | Evidence | Future gate |
| --- | --- | --- | --- |
| Multiple large `groupby`, `merge`, and `concat` paths define core calculations. | `high_risk_business_logic_sensitive` | `src/main.py`, `src/build_marts.py`, and `src/build_report.py`. | Stage/mart local regression and formula checks. |
| Row-wise `apply(axis=1)` is present in Stage source mix classification. | `medium_risk_pipeline_io` | `src/main.py` applies `classify_source_mix` row-wise after aggregation. | Stage contract validation and source_mix risk check. |
| `iterrows()` appears in service row creation and report/depth package generation. | `medium_risk_pipeline_io` | `src/main.py`, `src/rebuild_memo01_depth_package.py`, and scripts. | Selected local regression plus artifact comparison. |
| Repeated Excel QA reads are used after writing management workbooks. | `medium_risk_report_artifact` | `src/build_marts.py` validates Excel sheets with repeated `pd.read_excel()` calls. | Mart/report artifact validation before optimization. |

## Report / DOCX / Render Findings

| Finding | Classification | Evidence | Future gate |
| --- | --- | --- | --- |
| DOCX generation is spread across multiple modules. | `medium_risk_report_artifact` | `src/build_report.py`, `src/build_depth_mode_outputs.py`, `src/polish_docx_report.py`, `src/rebuild_memo01_depth_package.py`, and factory script use `Document()`. | Report artifact and render validation. |
| Render QA can invoke external tools. | `medium_risk_report_artifact` | `scripts/diagnose_docx_visual_quality.py` uses LibreOffice/Poppler-style subprocess paths. | Explicit render/DOCX/PDF validation only. |
| Chart and media artifacts are copied, counted, and embedded in DOCX paths. | `medium_risk_report_artifact` | Report/depth/factory modules inspect chart manifests and DOCX media. | Artifact validation matrix and render QA. |

## Ollama / LLM Path Findings

| Finding | Classification | Evidence | Future gate |
| --- | --- | --- | --- |
| Live Ollama calls have primary/fallback routing and long timeouts. | `blocked_without_business_approval` | `src/run_ollama_memo_pipeline.py`, `src/build_report.py`, and factory script. | Ollama/live LLM validation with explicit approval. |
| LLM sanitization and claim/evidence boundary checks are behavior-sensitive. | `high_risk_business_logic_sensitive` | `src/run_ollama_memo_pipeline.py` contains sanitization, judge, and evidence matrix logic. | Claim/evidence/LLM risk register gate. |
| Factory script is large and combines generation, rendering, QA, and package writes. | `blocked_without_business_approval` | `scripts/regenerate_memo01_memo02_ollama_factory.py` is a large orchestration script. | Separate design task before refactor. |

## Test Cost Findings

| Finding | Classification | Evidence | Future gate |
| --- | --- | --- | --- |
| Full test discovery is not public-data-free. | `low_risk_docs_or_checker_only` | Stage 4/5 docs and data-dependent tests reference local artifacts. | Keep CI data-free unless proven safe. |
| Data-dependent tests read Stage, mart, Excel, DOCX, and QA artifacts. | `medium_risk_pipeline_io` | `tests/test_output_contract.py`, `tests/test_mart_outputs.py`, and visual/package tests. | Local regression plan. |
| Public checks are intentionally narrow and fast. | `low_risk_docs_or_checker_only` | `repo-smoke.yml` runs only safety/config/test-strategy checks. | Preserve as CI baseline. |

## High-Risk Business Logic Zones

- Stage schema, grain, reconciliation, and source lineage: `high_risk_business_logic_sensitive`.
- p-fact reconciliation and player refund treatment: `high_risk_business_logic_sensitive`.
- IN / OUT / IN-OUT denominator and repeated monthly value semantics: `high_risk_formula_or_schema`.
- Mart formulas, risk levels, thresholds, rankings, and compact signal selection: `high_risk_formula_or_schema`.
- Claim/evidence/LLM boundary and unsupported claim guards: `high_risk_business_logic_sensitive`.

## Low-Risk Future Candidates

- Add docs/checker-only markers for new governance docs: `low_risk_docs_or_checker_only`.
- Add static command classification tests: `low_risk_docs_or_checker_only`.
- Split public data-free and local-only test documentation further: `low_risk_docs_or_checker_only`.
- Add dry-run inventory scripts that inspect tracked files only: `low_risk_docs_or_checker_only`.

## Blocked Candidates

- Formula, schema, row-grain, output contract, prompt, or QA gate changes without approval: `blocked_without_business_approval`.
- Optimizing p-fact reconciliation without Stage regression evidence: `blocked_without_business_approval`.
- Reworking mart formulas or signal classification without business approval: `blocked_without_business_approval`.
- Refactoring live Ollama generation or judge flow without explicit approval: `blocked_without_business_approval`.

## Recommended Next Stages

1. Stage 7 inspect-only profiling design: define timing probes and local benchmark commands without executing full pipeline.
2. Stage 8 local approved baseline run: execute selected local regression checks only after explicit authorization.
3. Stage 9 low-risk I/O fix candidates: start with duplicate reads or docs/checker-only improvements.
4. Stage 10 high-risk refactor design: prepare approval packet for formula/schema/report/LLM-sensitive changes.
