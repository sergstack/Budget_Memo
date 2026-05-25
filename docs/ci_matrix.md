# CI Matrix

This document defines the current CI policy and future CI lanes. It does not add local data, report-generation, or Ollama lanes.

## Current GitHub CI

Current GitHub Actions workflow:

The current GitHub Actions workflow is data-free only.

- `.github/workflows/repo-smoke.yml`

Current lane:

- `public_data_free`

Purpose:

- validate public repository safety;
- run data-free unit checks;
- verify memo-factory quality-gate config;
- verify the test strategy and CI governance markers.

Current commands:

```bash
python scripts/check_repo_public_safety.py
python -m unittest tests.test_repo_public_safety -q
python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
python scripts/check_test_strategy.py
python -m unittest tests.test_test_strategy -q
```

## Why Full Pipeline Is Excluded

The full pipeline requires ignored local corporate data and generated artifacts. Public CI must not depend on or generate:

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
- report, DOCX/PDF, chart, log, cache, or archive outputs

Public CI must not run `src/main.py`, `src/build_marts.py`, full test discovery, report generation, or Ollama/live LLM generation unless a future task explicitly approves and designs a safe lane.

## Future Possible CI Lanes

### data-free governance lane

Status: current.

Scope: repository safety, governance docs, public clone checks, quality-gate config, test-strategy markers.

### local-only regression lane

Status: future/manual.

Scope: stage/mart/output contract checks against local ignored data and artifacts.

Allowed in GitHub CI: no in the current repository state.

### artifact validation lane

Status: future/manual.

Scope: accepted report package validation, DOCX/PDF/render checks, chart/media presence, release manifests.

Allowed in GitHub CI: no in the current repository state.

### Ollama/manual lane

Status: future/manual.

Scope: live Ollama/LLM routing, memo generation, narrative QA.

Allowed in GitHub CI: no in the current repository state.

### performance/manual lane

Status: future/manual.

Scope: benchmark design for runtime, I/O, rendering, and scaling risk.

Allowed in GitHub CI: no in the current repository state.

## CI Expansion Rule

Any CI expansion beyond `public_data_free` requires explicit approval, a validation design, and a documented explanation of required local prerequisites, artifact writes, and data/security risk.
