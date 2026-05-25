# Stage Contract

Canonical name: `stage_main_full`.

Physical file: `02_stage/01_full_stage.csv`.

Role: full cleaned stage layer after raw ingestion and before mart generation.

It is the only user-facing stage CSV and the source for mart generation.

## Allowed in stage

- Cleaned, normalized, typed base fields.
- Base skeleton financial measures:
  - `План, EUR`
  - `Факт, EUR`
  - `IN-OUT, EUR`
- Technical and audit fields, including `source_file` and `source_row_id`.

`source_row_id` is grouped lineage after stage aggregation. It may contain more than one raw row id joined with ` | `.

## Forbidden in stage

- Derived business metrics, such as plan-fact deltas, absolute deviation, execution percentage, shares, MoM, or YoY.
- Risk labels.
- Materiality flags.
- Management conclusions or recommendations.

## Known limitations

- `load_timestamp` / `pipeline_run_id` is not currently present. Add it only as a future backward-compatible improvement after approval.
- A dedicated `rejected_rows` / validation errors artifact is not currently present. Add it only as a future backward-compatible improvement after approval.
- Period parsed from filename is a candidate period unless independently confirmed by source metadata or user instruction.

Any code, formula, grain, raw file, or output schema change related to this contract requires separate approval.
