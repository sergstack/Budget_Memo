# Project Next Memos Plan

## Step 0 — Validate Memo 01 Depth Outputs

Objective: confirm that depth semantics match business expectations.

- `standard`: accepted management memo.
- `short`: chart-led executive pack.
- `deep`: finance working package / slice workbook / evidence package.
- `action`: action tracker.

Acceptance criteria:

- Correct canonical folder: `06_reports/01_executive_yoy_mom_budget_memo/`.
- Correct active inventory: `06_reports/_inventory/report_inventory.md`.
- No use of generic `memo_01/` as active folder.
- Business owner accepts which depth artifacts are shareable.

## R1 Memo Sequence

1. `monthly_plan_fact_memo`
2. `planning_risk_memo`
3. `weekly_coo_cash_cost_memo`
4. `data_quality_blocker_memo`
5. `in_out_pressure_memo`

## 1. monthly_plan_fact_memo

Objective: explain closed-month budget execution.

Audience: CFO / Finance.

Source marts/slices:

- `mart_main_full_budget`
- `slice_plan_fact_article`
- `slice_plan_fact_article_cfo`
- `slice_plan_fact_counterparty`
- `slice_source_mix_summary`

Required charts:

- Top Plan-Fact deviations by ABS EUR.
- Plan-Fact by article/CFO.
- Source/QC limitations.
- IN context only where denominator is valid.

Required Excel workbook:

- Plan-Fact article and article-CFO sheets.
- Counterparty appendix if needed.
- Source/QC sheet.

LLM deep conclusion role: synthesize supported observations after deterministic claim candidates are prepared.

QA requirements:

- No service rows in expense deviation top lists.
- Execution % blank/statused where plan denominator is invalid.
- All visible labels in Russian.

Expected outputs:

- Standard DOCX.
- Slice workbook.
- QA report.

Acceptance criteria:

- All claims have evidence id/source slice.
- Limitations visible.
- No DOCX before report contract and data package.

## 2. planning_risk_memo

Objective: identify future budget risk relative to historical base.

Audience: CFO / Budget owners.

Source marts/slices:

- `slice_plan_vs_history_article`
- `slice_plan_vs_history_article_cfo`
- `slice_plan_without_history_base`
- `slice_planning_risk_candidates`

Required charts:

- Plan vs historical base by ABS EUR.
- Base availability / missing base.
- Planning risk localization.

Required Excel workbook:

- Planning risk by article.
- Planning risk by article/CFO.
- Missing base appendix.

LLM deep conclusion role: distinguish future risk, interpretation, and hypothesis.

QA requirements:

- Planning risk must not be described as actual execution.
- Base months and weak/no-base limitations visible.

Expected outputs:

- Standard DOCX.
- Deep workbook.
- Action tracker candidates.

Acceptance criteria:

- Future-risk wording preserved.
- No unsupported overrun/saving claims.

## 3. weekly_coo_cash_cost_memo

Objective: provide short operating view of MTD cost/cash movement and IN pressure.

Audience: COO.

Source marts/slices:

- `mart_flow_base_month`
- Plan-Fact article/CFO slices.
- MoM slices where period logic is valid.

Required charts:

- IN / OUT / IN-OUT movement.
- Top cost movements.
- IN pressure.

Required Excel workbook:

- MTD cost movement table.
- Flow base table.
- Action tracker.

LLM deep conclusion role: write concise operating synthesis, not calculate MTD.

QA requirements:

- Weekly/MTD period logic documented.
- IN ratios only with valid denominator scope.

Expected outputs:

- Short chart-led pack.
- Action workbook.

Acceptance criteria:

- No full evidence dump in COO body.
- No unsupported cause statements.

## 4. data_quality_blocker_memo

Objective: identify blockers to publishing management conclusions.

Audience: Finance / Data owner.

Source marts/slices:

- `slice_source_mix_summary`
- `slice_dq_flags`
- `slice_unmatched_or_excluded_rows`
- `slice_reconciliation_scope`

Required charts:

- Data limitations by row count.
- Data limitations by amount if applicable.
- Source mix.

Required Excel workbook:

- DQ flags.
- Reconciliation scope.
- Source mix.
- Blocker register.

LLM deep conclusion role: summarize blockers and limitations without overstating financial misstatement.

QA requirements:

- DQ Fail blocks management conclusion.
- Count and amount metrics use separate formatters.

Expected outputs:

- Standard DOCX.
- DQ workbook.
- Action tracker.

Acceptance criteria:

- Blocker vs limitation is explicit.
- No financial distortion claim without evidence.

## 5. in_out_pressure_memo

Objective: explain expense pressure relative to iGaming inflow.

Audience: CFO / COO.

Source marts/slices:

- `mart_flow_base_month`
- Plan-Fact slices with valid denominator status.
- IN normalization metrics.

Required charts:

- IN / OUT / IN-OUT trend.
- Top deviations to IN.
- Flow pressure signals.

Required Excel workbook:

- Flow base.
- Valid denominator rows.
- Excluded/blocked denominator rows.

LLM deep conclusion role: explain proportionality to inflow and limitations.

QA requirements:

- Definition Card for IN / OUT / IN-OUT required.
- IN-OUT must not be summed across ordinary article rows.
- Denominator status must be visible.

Expected outputs:

- Standard DOCX.
- Flow workbook.

Acceptance criteria:

- No IN-ratio claim with invalid denominator.
- Flow rows separated from expense rows.
