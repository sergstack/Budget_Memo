# Memo Factory Runbook

## Purpose

This runbook defines the reusable release standard for memo packages under `06_reports/`.
It freezes the accepted memo01 and memo02 lessons into a repeatable factory process.

## Default Doctrine

All analytical memo generation follows `99_docs/MODEL_ROUTING_MAX_CHAIN_DOCTRINE.md` by default.
Core rule: Code calculates. LLM writes. Judge cuts. Release ships only proven artifacts.

## Canonical Lifecycle

Use this lifecycle for every memo package:

1. inventory
2. logic review workbook
3. chart manifest
4. charts
5. source_refs/evidence
6. final MD/DOCX/XLSX
7. DOCX media check
8. render
9. text_qa
10. judge_preflight
11. final judge
12. release registry

Do not skip from inventory directly to final DOCX generation. Do not treat technical QA as business acceptance.

## Folder Rules

- Every memo package must live under one canonical folder: `06_reports/<memo_id>/`.
- Final user-facing outputs must stay under that package folder, normally in `final/`, `charts/`, `tables/`, `source_refs/`, and `qa/`.
- No final outputs may be created outside the package folder.
- `07_qa/` is reserved only for timestamped QA run artifacts.
- Old QA artifacts may remain for traceability, but the release registry must identify the latest accepted QA path.

## Logic Control

- Build or identify the logic review workbook before final generation when the memo has multiple analytical blocks, actions, or chart dependencies.
- The workbook must show what numbers are used, which slices support conclusions, which charts are used, which claims are allowed, which limitations apply, and which actions are candidate-only.
- Do not recalculate business formulas during final document generation unless the task explicitly authorizes that phase.

## Chart Standard

- Every final chart must have a manifest row.
- Every chart manifest row must include a non-empty limitation.
- Every chart image referenced by the manifest must physically exist.
- A chart without a limitation is not releasable.
- Charts must be embedded in final DOCX files; linked Markdown references alone are not enough.

## DOCX Standard

- Do not accept a package based only on DOCX existence.
- Do not accept a final DOCX with `0` embedded media when charts are required.
- DOCX `word/media/` count must meet the depth requirement before render/judge acceptance.
- LibreOffice render must pass or be explicitly blocked with a reason. On macOS, check `/Applications/LibreOffice.app/Contents/MacOS/soffice` if `soffice` is not in `PATH`.

## QA and Judge Standard

- `text_qa` must pass.
- `judge_preflight` must receive deterministic package facts: output paths, media counts, chart manifest status, chart existence, render status, action mode, and data/mart impact.
- Final judge payloads must not contradict deterministic preflight facts.
- Final judge acceptance is invalid without deterministic preflight summary.

## Data Boundary

- Report generation must not modify `02_stage/` or `03_marts/`.
- Do not rebuild marts during final memo generation.
- Do not change schemas or formulas during release consolidation.
- Run mtime or hash checks for `02_stage/` and `03_marts/` before release acceptance.

## Action Mode

- Action outputs default to `candidate_only`.
- Do not invent confirmed owners, due dates, action statuses, overdue charts, or status funnels.
- Confirmed actions require external confirmation and must be documented as such.

## Release Registry

After final judge acceptance, update `06_reports/release_registry.xlsx` and `06_reports/release_registry.md` with:

- accepted packages;
- depth outputs;
- QA status;
- DOCX media counts;
- chart manifest status;
- rendered PDF paths;
- data/mart impact;
- residual risks;
- next packages.

## Golden Memo Pack Validation

Golden Memo Pack validation is required before claiming factory production readiness.
Current `golden_memo_pack` status is `active_candidate` and `production_ready=false` until a real accepted golden case and negative-case stop tests pass.

## Doctrine Enforcement Layer

The offline enforcement layer is defined by `config/memo_factory_quality_gates.yml` and `config/memo_factory_routing_config.json`.
Use `scripts/verify_memo_factory_quality_gates.py` for stop-rule config checks, `scripts/verify_claim_freeze_for_release.py` for claim-freeze release checks, `scripts/validate_release_manifest.py` for release manifest validation, and `scripts/verify_high_risk_release_readiness.py` for high-risk release readiness checks.
This layer is not live generation wiring unless a separate production wiring task explicitly activates it.
