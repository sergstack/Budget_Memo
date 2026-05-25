# Project Artifact Inventory

## Stage

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `02_stage/01_full_stage.csv` | Accepted Stage main artifact / `stage_main_full` analogue | accepted | MART generation | No load timestamp / pipeline run id yet; additive future improvement only. |
| `02_stage/audit/` | Stage audit outputs | generated | Stage QA | Do not change without approval. |

## MART Artifacts

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `03_marts/mart_main_full_budget.parquet` | Full MART source | accepted | slices, signal catalog | Core formulas must not change without approval. |
| `03_marts/mart_flow_base_month.parquet` | IN / OUT / IN-OUT monthly flow base | accepted | IN context, flow charts | IN denominator rules must be respected. |
| `03_marts/mart_signal_catalog_full.parquet` | Traceable signal catalog | accepted | compact mart, memos, actions | Risk requires risk_basis. |
| `03_marts/mart_main_compact_executive_yoy_mom.parquet` | Compact source for executive memo | accepted | memo 01 | Executive content should come from compact layer. |
| `03_marts/slice_*.parquet` | Analytical slices | accepted/generated | Excel, charts, memo data packages | One grain per management sheet. |
| `03_marts/mart_full_package.xlsx` | Management MART workbook | accepted/generated | finance review | Excel-visible labels must remain Russian. |

## Profile Artifacts

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `03_marts/memo_profile_catalog.parquet` | 18 memo profile catalog | accepted | readiness, report planning | Governance fields define publish rules. |
| `03_marts/profile_readiness_matrix.parquet` | Readiness by profile | accepted | memo planning | Blocked/partial/ready must be respected. |
| `03_marts/profile_preview_index.parquet` | Preview index | accepted | profile planning | Preview only is not final memo. |
| `03_marts/memo_depth_mode_catalog.parquet` | Depth mode catalog | accepted | output policy | Depth semantics clarified in `PROJECT_DEPTH_MODES.md`. |

## Chart Artifacts

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `04_charts/chart_catalog.parquet` | Technical chart catalog | accepted | report generation | Captions must not exceed evidence. |
| `04_charts/chart_catalog.xlsx` | Management chart catalog | accepted | review | Visible labels must remain Russian. |
| `04_charts/chart_data/*.parquet` | Chart datasets | accepted | chart images | Do not change source logic without QA finding. |
| `04_charts/chart_specs/*.json` | Chart specs | accepted | chart rendering | Chart role and memo placement are controlled. |
| `04_charts/images/*.png` | Chart images | accepted | DOCX/short pack | Muted executive palette applied. |

## LLM Package Artifacts

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `05_llm_package/executive_yoy_mom_draft_data_package.json` | Deterministic memo data package | accepted | memo draft | No final prose here. |
| `05_llm_package/executive_yoy_mom_claim_candidates.xlsx` | Claim candidates | accepted | grounding QA | Every important claim needs evidence. |
| `05_llm_package/executive_yoy_mom_evidence_map.xlsx` | Evidence map | accepted | memo and appendix | Evidence should not overload executive body. |
| `05_llm_package/deep_conclusion_input.json` | Ollama synthesis input | accepted | deep conclusion layer | LLM must not calculate. |

## Report Artifacts

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `06_reports/01_executive_yoy_mom_budget_memo/final/01_executive_yoy_mom_budget_memo__standard__2026-05-21__final.docx` | Accepted standard memo | accepted | management review | Production readiness not claimed. |
| `06_reports/01_executive_yoy_mom_budget_memo/final/01_executive_yoy_mom_budget_memo__short__2026-05-21__final.docx` | Chart-led executive pack | generated | business review | Needs review before external use. |
| `06_reports/01_executive_yoy_mom_budget_memo/tables/01_executive_yoy_mom_budget_memo__deep__2026-05-21__slices.xlsx` | Finance working package | generated | finance review | Deep is not narrative memo. |
| `06_reports/01_executive_yoy_mom_budget_memo/final/01_executive_yoy_mom_budget_memo__action__2026-05-21__final.xlsx` | Action tracker | generated | Finance PMO / owners | Owner/due/status require confirmation. |
| `06_reports/01_executive_yoy_mom_budget_memo/source_refs/deep_conclusion_draft.md` | Preserved Ollama deep conclusion | generated/reference | source refs | Narrative synthesis only. |

## QA Artifacts

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `07_qa/mart_rebuild_qa_report.json` | MART rebuild QA | accepted | MART acceptance | Deterministic QA. |
| `07_qa/memo_profile_catalog_qa_report.json` | Profile QA | accepted | profile acceptance | Confirms 18 profiles. |
| `07_qa/depth_modes_qa.json` | Depth mode QA | accepted | output policy | Semantics further clarified in project docs. |
| `06_reports/01_executive_yoy_mom_budget_memo/qa/memo_01__depth_outputs_qa.json` | Memo 01 depth output QA | pass | report folder acceptance | Confirms canonical folder and active inventory. |

## Archive Folders

| Path | Purpose | Status | Used by | Risk / notes |
|---|---|---|---|---|
| `99_archive/old_downstream_before_mart_rebuild_20260521_1252/` | Archive before MART rebuild | archived | rollback/reference | Not active. |
| `99_archive/report_cleanup_before_reorg_2026-05-21/` | Old unstructured report archive | archived | rollback/reference | Not active. |
| `99_archive/report_depth_output_cleanup_2026-05-21_1828/` | Superseded depth-output cleanup | archived | rollback/reference | Not active. |
| `99_archive/report_depth_semantics_fix_2026-05-21_1843/` | Generic folder / 99_inventory archive | archived | rollback/reference | Not active. |

## Active Report Folder

```text
06_reports/01_executive_yoy_mom_budget_memo/
```

## Legacy Folders / Files

- `06_reports/memo_01/`: archived; not active.
- `06_reports/99_inventory/`: archived; active inventory is `_inventory`.
- Old `final_memo.*`: archived; must not be used.
