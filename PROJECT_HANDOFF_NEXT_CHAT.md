# Project Handoff For Next Chat

## Project Objective

Build an analytics factory for 18 budget management memos from accepted Stage and MART layers, with deterministic calculations first and LLM narrative only after evidence is prepared.

## Completed Layers

- RAW preserved under `01_raw/`.
- Stage accepted: `02_stage/01_full_stage.csv`.
- MART rebuilt and accepted: full budget mart, flow base, signal catalog, compact executive mart, slices, QA.
- Memo profiles: 18-profile catalog and readiness matrix created.
- Chart package: accepted for `executive_yoy_mom_budget_memo`.
- Report contract and draft data package: accepted.
- Revised memo and DOCX: accepted and visually rendered.
- Ollama deep conclusion layer: added as synthesis layer, not calculation source.
- Report folder semantics corrected to profile-named memo folder.

## Accepted Artifacts

- Stage: `02_stage/01_full_stage.csv`.
- Main MART: `03_marts/mart_main_full_budget.parquet`.
- Flow MART: `03_marts/mart_flow_base_month.parquet`.
- Signal catalog: `03_marts/mart_signal_catalog_full.parquet`.
- Compact memo MART: `03_marts/mart_main_compact_executive_yoy_mom.parquet`.
- Memo profile catalog: `03_marts/memo_profile_catalog.parquet`.
- Chart catalog: `04_charts/chart_catalog.parquet`, `04_charts/chart_catalog.xlsx`.
- LLM package: `05_llm_package/executive_yoy_mom_draft_data_package.json`.
- Deep conclusion input: `05_llm_package/deep_conclusion_input.json`.
- Active first memo folder: `06_reports/01_executive_yoy_mom_budget_memo/`.

## Current Folder Structure

```text
06_reports/
  _inventory/
  01_executive_yoy_mom_budget_memo/
    final/
    tables/
    qa/
    source_refs/
  02_monthly_plan_fact_memo/
  ...
  18_board_level_budget_summary/
  99_shared/
  99_templates/
```

## First Memo Status

Profile: `executive_yoy_mom_budget_memo`.

Accepted standard version:

```text
06_reports/01_executive_yoy_mom_budget_memo/final/01_executive_yoy_mom_budget_memo__standard__2026-05-21__final.docx
```

Depth outputs exist:

- `standard`: accepted management memo.
- `short`: chart-led executive pack, needs business review before use.
- `deep`: finance working package / slice workbook.
- `action`: operating action tracker.

## Naming Rules

Use:

```text
<memo_number>__<memo_profile>__<depth_label>__<YYYY-MM-DD>__<status>.<ext>
```

Example:

```text
01_executive_yoy_mom_budget_memo__standard__2026-05-21__final.docx
```

## Depth Modes

- `short`: chart-led executive pack, 5-7 bullets, 3-5 charts, minimal text.
- `standard`: accepted management memo with compact evidence references.
- `deep`: finance working package with slices, evidence, methods, QA, limitations.
- `action`: action tracker with owner, due date, status, confirmation, escalation.

## Priority Plan For Next Memos

R1 next sequence:

1. `monthly_plan_fact_memo`
2. `planning_risk_memo`
3. `weekly_coo_cash_cost_memo`
4. `data_quality_blocker_memo`
5. `in_out_pressure_memo`

## Strict Forbidden Actions

- Do not change Stage.
- Do not change raw files.
- Do not change MART formulas.
- Do not change chart data.
- Do not generate final DOCX before contract/data package/QA.
- Do not use old `final_memo.docx`.
- Do not claim production readiness.
- Do not use LLM for calculations.

## Immediate Next Task

Validate `memo_01` depth outputs against business expectations, then create the controlled report contract and data package for `monthly_plan_fact_memo`.
