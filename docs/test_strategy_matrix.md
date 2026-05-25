# Test Strategy Matrix

This matrix separates public data-free checks from local data-dependent validation. It does not authorize full pipeline, report generation, or Ollama/live LLM execution by itself.

## Profile Summary

| Profile | Purpose | GitHub CI | May Write Ignored Artifacts | Risk |
| --- | --- | --- | --- | --- |
| `public_data_free` | Validate repository safety and data-free governance checks. | Yes | No | Low |
| `local_data_dependent` | Validate stage, mart, and output contracts against local ignored data. | No | Yes | Medium |
| `report_generation` | Validate report, DOCX/PDF/Excel, chart, render, and package outputs. | No | Yes | High |
| `ollama_live_llm` | Validate live Ollama/LLM generation and memo synthesis paths. | No | Yes | High |
| `contract_regression` | Validate schemas, contracts, doctrine, and accepted text fixtures. | Partial, only when data-free | No by default | Medium |
| `performance_future` | Measure runtime, repeated I/O, rendering cost, and scaling risk. | No | Possible | Medium |

## public_data_free

Purpose: prove that the public repository is safe to clone, basic governance files exist, and data-free config checks pass.

What it proves:

- forbidden data/artifact files are not tracked;
- required public governance docs and templates exist;
- quality-gate config is parseable by the verifier;
- public test-strategy docs and CI policy markers are present.

What it does not prove:

- stage/mart correctness;
- financial reconciliations;
- report rendering;
- accepted package completeness;
- Ollama/live LLM behavior.

Safe environment: public GitHub clone or local checkout without corporate data.

Commands:

```bash
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
python3 scripts/check_test_strategy.py
python3 -m unittest tests.test_test_strategy -q
```

Required local prerequisites: Python and repository dependencies. No corporate data, generated artifacts, Ollama, or LibreOffice required.

Allowed in GitHub CI: yes.

May write ignored artifacts: no.

Owner/reviewer expectations: repo maintainers and reviewers verify these checks for docs, CI, governance, and safety-tooling PRs.

## local_data_dependent

Purpose: validate pipeline behavior against local ignored corporate data and generated stage/mart layers.

What it proves:

- selected stage and mart contracts hold for local data;
- output contract tests pass against available local artifacts;
- local accepted inputs are compatible with current code.

What it does not prove:

- public clone readiness;
- report rendering completeness unless report checks are also run;
- Ollama/live LLM quality.

Safe environment: authorized local environment with ignored data layers present.

Commands:

```bash
python3 src/main.py
python3 src/build_marts.py
python3 -m unittest tests.test_output_contract -q
python3 -m unittest tests.test_mart_outputs -q
```

Required local prerequisites: `01_raw/`, local stage/mart/output fixtures as needed, and explicit task authorization.

Allowed in GitHub CI: no.

May write ignored artifacts: yes.

Owner/reviewer expectations: data/pipeline owner verifies input layers, output layers, periods, currencies, and reconciliation assumptions.

## report_generation

Purpose: validate memo/report package generation and rendering outputs.

What it proves:

- report-generation commands can produce local artifacts;
- DOCX/PDF/Excel/render checks can run in the local environment;
- accepted-package smoke checks can find expected local files when present.

What it does not prove:

- public clone readiness;
- live LLM generation unless paired with `ollama_live_llm`;
- financial correctness beyond the validated input package.

Safe environment: authorized local environment with generated inputs and rendering tools.

Commands are task-specific and may include accepted-package verification:

```bash
python3 scripts/verify_accepted_ollama_report_packages.py
```

Required local prerequisites: generated report package folders, chart/media artifacts, DOCX/PDF tooling when applicable, and explicit task authorization.

Allowed in GitHub CI: no.

May write ignored artifacts: yes.

Owner/reviewer expectations: report owner verifies generated artifacts, render QA, package manifests, and release readiness.

## ollama_live_llm

Purpose: validate live Ollama/LLM routing and memo synthesis behavior.

What it proves:

- local Ollama endpoint or configured LLM path is reachable;
- generation scripts can run in the authorized local environment;
- generated narratives can be checked by downstream QA when available.

What it does not prove:

- deterministic reproducibility across machines;
- public clone readiness;
- data correctness without accepted evidence packages.

Safe environment: authorized local machine with Ollama/live LLM access and required local packages.

Commands are task-specific and may include memo factory generation scripts only with explicit approval.

Required local prerequisites: Ollama/live LLM service, local evidence/LLM packages, output folders, and explicit task authorization.

Allowed in GitHub CI: no.

May write ignored artifacts: yes.

Owner/reviewer expectations: memo/report owner reviews grounding, unsupported claims, final QA, and generated artifacts.

## contract_regression

Purpose: validate stable contracts, doctrine, and fixtures without broad pipeline execution.

What it proves:

- schema/doctrine fixtures remain compatible;
- selected contract tests pass in the current environment;
- data-free contract tests can protect governance and prompt rules.

What it does not prove:

- full local data pipeline behavior unless data-dependent contract tests are authorized;
- report rendering or live LLM behavior.

Safe environment: public CI only for contract tests that are explicitly data-free; local environment for data-dependent contract tests.

Commands may include selected test modules, not full discovery by default:

```bash
python3 -m pytest tests/test_golden_memo_pack_contract.py -q
python3 -m pytest tests/test_memo_factory_doctrine_enforcement.py -q
```

Required local prerequisites: depends on the selected module. Confirm before adding to CI.

Allowed in GitHub CI: only if proven data-free.

May write ignored artifacts: no by default.

Owner/reviewer expectations: contract owner verifies that no schemas, prompts, formulas, or output contracts changed without approval.

## performance_future

Purpose: create a future lane for runtime and scaling risk without changing business logic.

What it proves:

- runtime trends;
- repeated file I/O hotspots;
- report rendering cost;
- candidate performance regressions after separate benchmark design.

What it does not prove:

- financial correctness;
- output contract validity;
- public clone readiness.

Safe environment: local benchmark environment with approved data subset or synthetic benchmark fixtures that cannot be confused with corporate data.

Commands: not defined yet. Add only after a separate benchmark design task.

Required local prerequisites: approved benchmark design and explicit authorization.

Allowed in GitHub CI: no in the current repository state.

May write ignored artifacts: possible.

Owner/reviewer expectations: performance changes require contract tests and reviewer approval before implementation.

## Explicit Defaults

- `python3 scripts/check_repo_public_safety.py` is `public_data_free`.
- `python3 -m unittest tests.test_repo_public_safety -q` is `public_data_free`.
- `python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml` is `public_data_free`.
- `python3 scripts/check_test_strategy.py` is `public_data_free`.
- `python3 -m unittest tests.test_test_strategy -q` is `public_data_free`.
- Full `python3 -m unittest discover -s tests -q` is not public-data-free by default.
- `src/main.py`, `src/build_marts.py`, report generation, DOCX/PDF rendering, and Ollama/live LLM generation are local and explicit-approval only.
