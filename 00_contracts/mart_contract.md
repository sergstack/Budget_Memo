# Mart Contract

Production mart tables are Parquet files in `03_marts/` with stable snake_case columns. They do not contain signals, evidence, recommendations, hypotheses, or memo text.

## Canonical main mart mapping

| Canonical name | Physical file | Role | Notes |
|---|---|---|---|
| `mart_main_full` | `03_marts/mart_main_full_budget.parquet` | Main full analytical mart | Source for slices and downstream analytics |
| `mart_main_compact` | `03_marts/mart_main_compact_executive_yoy_mom.parquet` | Compact executive / LLM-friendly mart | Also covers current `mart_main_tz` role |
| `mart_main_tz` | not separate physical file | Task / LLM compact representation | Currently represented by `mart_main_compact` |
| `slice_*.parquet` | `03_marts/slice_*.parquet` | Derived analytical slices | Must be derived from `mart_main_full` |

`mart_main_full_budget.parquet` is the current implementation of the canonical `mart_main_full`.

`mart_main_compact_executive_yoy_mom.parquet` is the current compact / TZ implementation.

## Signal catalog

`03_marts/mart_signal_catalog_full.parquet` is a derived signal/evidence catalog.

It is not the canonical `mart_main_full` and does not replace `mart_main_full_budget.parquet`.

Signal, evidence, recommendation, action, hypothesis, and memo-support fields in `mart_signal_catalog_full` do not redefine the production mart table contract above.

## Slice rule

New analytical slices must derive from `03_marts/mart_main_full_budget.parquet`, not from raw or stage directly, unless explicitly approved in task acceptance criteria.
