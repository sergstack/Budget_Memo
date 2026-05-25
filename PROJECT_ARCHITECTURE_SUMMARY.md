# Project Architecture Summary

## Architecture

```text
RAW
-> Stage
-> MART
-> slices / signal catalog / compact MART
-> chart package
-> deterministic memo data package
-> LLM / Ollama synthesis
-> Markdown / DOCX / Excel outputs
-> QA / acceptance
```

## RAW

Raw source files live in `01_raw/` and are preserved. Raw files are not edited by report, MART, or memo generation tasks.

## Stage

Accepted Stage artifact:

```text
02_stage/01_full_stage.csv
```

It is the project `stage_main_full` analogue and source for MART generation. Stage may contain base skeleton measures such as `План`, `Факт`, and `IN-OUT`; it must not contain management conclusions, risk labels, materiality flags, or derived executive conclusions.

## MART

Main accepted MART artifacts:

- `03_marts/mart_main_full_budget.parquet`
- `03_marts/mart_flow_base_month.parquet`
- `03_marts/mart_signal_catalog_full.parquet`
- `03_marts/mart_main_compact_executive_yoy_mom.parquet`

MART owns formulas, metrics, rankings, risk basis, and signal classification.

## Slices

Slices live in `03_marts/slice_*.parquet`. Slices must be built from `mart_main_full_budget` or accepted derived marts. One management Excel sheet must have one clear grain.

## Signal Catalog

`mart_signal_catalog_full` is the traceable signal layer. It provides signal type, risk basis, confidence, recommended action, memo section, evidence id, source slice, QA status, and limitations.

## Memo Profiles

Memo profile artifacts:

- `03_marts/memo_profile_catalog.parquet`
- `03_marts/profile_readiness_matrix.parquet`
- `03_marts/profile_preview_index.parquet`
- `03_marts/memo_depth_mode_catalog.parquet`

Profiles define audience, purpose, source signal types, readiness, stop conditions, output layer, and governance rules.

## Chart Package

Accepted chart package:

- `04_charts/chart_catalog.parquet`
- `04_charts/chart_catalog.xlsx`
- `04_charts/chart_data/*.parquet`
- `04_charts/chart_specs/*.json`
- `04_charts/images/*.png`

Charts must use accepted MART/slices, Russian visible labels, muted executive palette, evidence-bounded captions, and no raw/stage direct reads.

## LLM / Ollama Deep Conclusion Layer

LLM/Ollama is a narrative synthesis layer only. It consumes deterministic evidence, claim candidates, chart captions, limitations, risk basis, confidence rules, action candidates, and depth mode.

LLM must not calculate metrics, invent numbers, invent causes, or override QA limitations.

## DOCX / Excel Outputs

Current active first memo folder:

```text
06_reports/01_executive_yoy_mom_budget_memo/
```

Depth outputs:

- `standard`: accepted management memo DOCX.
- `short`: chart-led executive pack DOCX.
- `deep`: finance working package workbook.
- `action`: action tracker workbook.

## QA / Acceptance

QA artifacts live in `07_qa/` and memo-specific `qa/` folders. Acceptance requires deterministic source checks, evidence traceability, visible limitations, no unsupported claims, and render QA for DOCX before sharing.

## Principles

- Deterministic calculations before LLM narrative.
- All slices from `mart_main_full_budget` or accepted derived marts.
- Executive content from compact layer; evidence from full layer.
- EUR before percentages.
- Facts, calculations, interpretations, recommendations, hypotheses, and limitations must be separated.
