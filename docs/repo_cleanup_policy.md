# Repository Cleanup Policy

This policy documents when cleanup is allowed. It does not delete or modify files by itself.

## Generated Artifacts

Generated artifacts belong in ignored local folders such as `artifacts/`, `output/`, `outputs/`, `runs/`, `logs/`, `tmp/`, `temp/`, and `.cache/`. Do not commit them unless a task explicitly reclassifies a small text fixture as safe.

## Local Data

Corporate inputs and local exports must stay out of Git. Raw workbooks, CSV/TSV files, Parquet files, databases, archives, DOCX/PDF/PNG outputs, logs, credentials, and private configs are local-only by default.

## Raw, Stage, Mart, Report, And QA Layers

The following folders are local/ignored layers and must not be cleaned or changed without explicit task approval:

- `01_raw/`
- `02_stage/`
- `03_marts/`
- `04_charts/`
- `04_signals/`
- `05_evidence/`
- `05_llm_package/`
- `06_reports/`
- `07_qa/`
- `99_archive/`

Preserve raw inputs. Do not delete accepted QA, audit, release, or archive artifacts unless a task explicitly authorizes deletion and rollback has been considered.

## Cache And Temporary Files

Cache files such as `__pycache__/`, `.pytest_cache/`, `.DS_Store`, `.ipynb_checkpoints/`, temporary logs, and local render scratch files may be removed locally when they are untracked and not needed for debugging. Do not remove tracked files without review.

## Branch Cleanup

Do not delete local or remote branches automatically. Branch cleanup requires explicit approval and should happen only after confirming the branch has been merged or superseded.

## Documentation Duplicates

Documentation duplicates should be consolidated only after confirming the canonical source. Until then, document the duplication in an audit or backlog and avoid deleting historical handoff context.

## Old Task Packages

Old task packages under `Codex_Tasks/`, `99_docs/`, or project handoff docs may preserve decision history. Prefer archiving guidance or README pointers over deletion unless the user explicitly approves removal.

## Performance Backlog

Performance cleanup must be planned separately from repository hygiene. Do not optimize code, alter formulas, move layers, or change output contracts under a cleanup-only task.

## When Deletion Is Allowed

Deletion is allowed only when all conditions hold:

- The file is untracked or explicitly approved for removal.
- The file is confirmed generated, cache, temporary, or superseded.
- The removal does not affect formulas, schemas, output contracts, QA evidence, auditability, or rollback.
- The deletion is reported with verification.

## When Only Documentation Is Allowed

Use documentation-only cleanup when a file may contain business context, accepted outputs, audit evidence, branch history, or financial-control decisions. In those cases, record the risk and defer removal.
