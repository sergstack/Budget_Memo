# Analytics Main Files Standard

## Purpose

This standard defines the minimum canonical data structure for analytical packages in `[Analytics]`.

The goal is to prevent ad-hoc analysis from disconnected extracts and to make every analytical conclusion traceable to a controlled full mart.

## Canonical flow

```text
RAW → stage_main_full → mart_main_full → mart_main_tz / mart_main_compact → slices → memo / dashboard / Codex handoff
```

## Required files / objects

| Object | Required | Role | Source of truth |
|---|---:|---|---|
| `stage_main_full` | yes | cleaned normalized analytical stage | no |
| `mart_main_full` | yes | canonical full analytical mart | yes |
| `mart_main_tz` / `mart_main_compact` | yes | compact task-zone representation | no |
| slices | optional | focused views for analysis | no |
| memo package | optional | LLM/report context | no |

## `stage_main_full`

`stage_main_full` is the normalized layer after raw ingestion and cleaning.

Must include:

- explicit row grain;
- normalized dates;
- normalized dimensions;
- normalized metric columns;
- source references if available;
- technical QA columns when needed.

Must not include:

- final management conclusions;
- LLM-written text;
- arbitrary manual slices as source of truth;
- silent business definition changes.

## `mart_main_full`

`mart_main_full` is the main analytical mart.

Must include:

- all dimensions required for downstream slices;
- all approved metrics;
- reconciliation totals;
- materiality fields if used;
- status / flag fields if used;
- documented grain.

Rule:

```text
Every slice must be reproducible from mart_main_full.
```

## `mart_main_tz` / `mart_main_compact`

This is a compact mart for a specific task, prompt, memo, review, or management pack.

Must include:

- task-relevant dimensions;
- task-relevant metrics;
- evidence references where possible;
- no hidden independent logic.

Must not:

- replace `mart_main_full`;
- use raw data directly when `mart_main_full` exists;
- change formulas silently;
- omit fields that are required to verify the conclusion.

## Slice derivation rule

Correct:

```text
mart_main_full → slice_by_period
mart_main_full → slice_by_cfo
mart_main_full → slice_by_counterparty
mart_main_full → mart_main_tz
```

Incorrect:

```text
raw_file → slice_by_period → final conclusion
compact_file → another compact_file → final conclusion
```

## Minimal metadata block

Each analytical package should document:

```yaml
package_name:
period:
source_files:
stage_main_full:
mart_main_full:
mart_main_tz_or_compact:
row_grain:
metrics:
slices:
reconciliation_status:
known_limitations:
```

## Acceptance phrase

Slices derive from `mart_main_full`.
