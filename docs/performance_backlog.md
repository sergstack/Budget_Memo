# Performance Backlog

This backlog records future candidates only. Do not implement any item without a separate approved task and the required regression gate.

## PERF-001

id: `PERF-001`

title: Review duplicate DDS workbook read

area: Excel reading and xlsx cleaning

observed pattern: `src/main.py` reads a DDS workbook twice consecutively in `build_dds()`.

expected benefit: reduce redundant XLSX cleaning/read cost during Stage build.

risk class: `medium_risk_pipeline_io`

files likely involved: `src/main.py`

required regression gate: `stage_contract_validation`

commands required before implementation:

```bash
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/check_test_strategy.py
python3 -m unittest tests.test_test_strategy -q
```

commands forbidden unless approved: `python3 src/main.py`, full test discovery, report generation, rendering, Ollama/live LLM.

acceptance criteria for future implementation: Stage output and reconciliation metrics remain unchanged for an authorized local baseline.

## PERF-002

id: `PERF-002`

title: Evaluate reusable cleaned XLSX cache

area: Excel reading and xlsx cleaning

observed pattern: `read_xlsx()` cleans source XLSX files into a temporary path before reading.

expected benefit: reduce repeated cleaning cost if the same workbook is read more than once.

risk class: `medium_risk_pipeline_io`

files likely involved: `src/main.py`

required regression gate: `stage_contract_validation`

commands required before implementation: public data-free checks plus authorized Stage baseline.

commands forbidden unless approved: report generation, rendering, Ollama/live LLM.

acceptance criteria for future implementation: cleaned-cache behavior is deterministic and Stage output remains unchanged.

## PERF-003

id: `PERF-003`

title: Assess row-wise source_mix classification

area: DataFrame `apply(axis=1)`

observed pattern: `src/main.py` uses row-wise `aggregated.apply(classify_source_mix, axis=1)`.

expected benefit: potential speedup via vectorized classification.

risk class: `high_risk_business_logic_sensitive`

files likely involved: `src/main.py`

required regression gate: `stage_contract_validation`, source_mix comparison, artifact diff.

commands required before implementation: public data-free checks plus authorized Stage local regression.

commands forbidden unless approved: changing source_mix semantics, formulas, or Stage schema.

acceptance criteria for future implementation: every `source_mix` value matches the approved baseline exactly.

## PERF-004

id: `PERF-004`

title: Profile mart groupby / merge / concat paths

area: large groupby / merge / concat paths

observed pattern: `src/build_marts.py` is the largest module and contains many pandas aggregation and join paths.

expected benefit: identify actual runtime hotspots before refactor.

risk class: `high_risk_formula_or_schema`

files likely involved: `src/build_marts.py`

required regression gate: `mart_contract_validation`

commands required before implementation: public data-free checks plus authorized mart baseline and formula comparison.

commands forbidden unless approved: formula, schema, row-grain, risk-ranking, or signal classification changes.

acceptance criteria for future implementation: all selected mart formulas, row counts, schemas, and QA checks match the approved baseline.

## PERF-005

id: `PERF-005`

title: Reduce repeated Excel validation reads

area: repeated file reads

observed pattern: `src/build_marts.py` writes the management workbook and then performs repeated `pd.read_excel()` validation.

expected benefit: reduce QA validation time by reusing workbook metadata or cached sheet reads.

risk class: `medium_risk_report_artifact`

files likely involved: `src/build_marts.py`

required regression gate: `mart_contract_validation` and `report_artifact_validation`

commands required before implementation: public data-free checks plus authorized mart/report artifact validation.

commands forbidden unless approved: changing workbook visible columns, sheet names, or QA rules.

acceptance criteria for future implementation: workbook QA verdicts remain unchanged.

## PERF-006

id: `PERF-006`

title: Split DOCX generation/render responsibilities

area: DOCX generation

observed pattern: DOCX generation appears across several source and factory modules.

expected benefit: clearer ownership and easier targeted validation.

risk class: `medium_risk_report_artifact`

files likely involved: `src/build_report.py`, `src/build_depth_mode_outputs.py`, `src/polish_docx_report.py`, `src/rebuild_memo01_depth_package.py`, `scripts/regenerate_memo01_memo02_ollama_factory.py`

required regression gate: `report_artifact_validation` and `render_docx_pdf_validation`

commands required before implementation: public data-free checks plus authorized report/render validation.

commands forbidden unless approved: report generation, DOCX/PDF rendering, or changing final artifacts.

acceptance criteria for future implementation: generated DOCX media, render QA, and report package manifests match accepted expectations.

## PERF-007

id: `PERF-007`

title: Isolate chart/render pipeline validation

area: chart/render pipeline

observed pattern: chart manifests, chart images, DOCX media, and render QA are coupled in report package paths.

expected benefit: reduce manual review cost and improve failure localization.

risk class: `medium_risk_report_artifact`

files likely involved: `src/build_chart_package.py`, `src/build_report.py`, `scripts/diagnose_docx_visual_quality.py`

required regression gate: `report_artifact_validation` and `render_docx_pdf_validation`

commands required before implementation: public data-free checks plus authorized artifact/render checks.

commands forbidden unless approved: rendering, report generation, changing chart specs, changing visible report outputs.

acceptance criteria for future implementation: chart/media manifest checks remain equivalent or stricter.

## PERF-008

id: `PERF-008`

title: Separate Ollama generation from deterministic package validation

area: Ollama/live LLM generation

observed pattern: LLM generation paths include routing, fallback, judge, package writes, and QA.

expected benefit: make deterministic preflight cheaper and reduce accidental live LLM execution.

risk class: `blocked_without_business_approval`

files likely involved: `src/run_ollama_memo_pipeline.py`, `scripts/regenerate_memo01_memo02_ollama_factory.py`

required regression gate: `ollama_live_llm_validation` plus claim/evidence review.

commands required before implementation: public data-free checks plus explicit Ollama/local package validation.

commands forbidden unless approved: Ollama/live LLM calls, report generation, final artifact writes.

acceptance criteria for future implementation: no unsupported claims, no invented numbers, and judge/final QA behavior preserved.

## PERF-009

id: `PERF-009`

title: Split public and local test suite lanes further

area: test suite split

observed pattern: full test discovery is not public-data-free by default.

expected benefit: clearer CI boundaries and lower accidental data-dependent test execution risk.

risk class: `low_risk_docs_or_checker_only`

files likely involved: `TESTING.md`, `docs/test_strategy_matrix.md`, `scripts/check_test_strategy.py`, `tests/test_test_strategy.py`

required regression gate: public data-free checks.

commands required before implementation: current public data-free checks.

commands forbidden unless approved: full test discovery and local pipeline commands.

acceptance criteria for future implementation: CI remains data-free and checker coverage increases.

## PERF-010

id: `PERF-010`

title: Design local-only performance benchmark lane

area: CI data-free vs local lanes

observed pattern: performance_future is documented but has no benchmark commands.

expected benefit: define measurable before/after evidence before optimization.

risk class: `medium_risk_pipeline_io`

files likely involved: docs and future benchmark tooling.

required regression gate: `performance_future` design plus selected local regression checks.

commands required before implementation: public data-free checks and explicit local benchmark approval.

commands forbidden unless approved: full pipeline, report generation, rendering, Ollama/live LLM.

acceptance criteria for future implementation: benchmark commands are reproducible and do not commit generated artifacts.
