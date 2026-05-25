# Local Regression Plan

This plan defines local-only regression profiles for data-dependent validation. These checks are not public-data-free, require local ignored data or artifact layers, must not run in GitHub public CI, and require explicit task authorization before execution.

## stage_contract_validation

Purpose: validate the Stage output contract and reconciliation-sensitive stage behavior.

What it proves:

- `02_stage/01_full_stage.csv` can be produced or inspected in the authorized local environment;
- Stage columns, grain, key fields, and base financial measures remain compatible with `SPEC.md`;
- reconciliation-sensitive outputs can be checked against local inputs and audit files.

What it does not prove:

- mart formulas beyond the Stage boundary;
- report rendering;
- Ollama/live LLM behavior;
- public clone readiness.

Prerequisites:

- explicit task authorization;
- local `01_raw/` source workbooks;
- existing or generated `02_stage/` artifacts;
- clear period and currency assumptions.

Commands:

```bash
python3 src/main.py
python3 -m unittest tests.test_output_contract -q
```

Expected outputs:

- `02_stage/01_full_stage.csv`;
- `02_stage/audit/` diagnostic files;
- reconciliation stdout from `src/main.py`;
- passing output-contract checks when local artifacts are present.

Allowed environment: authorized local machine only.

May write ignored artifacts: yes.

Stop rules:

- reconciliation failures or unexplained tolerance drift;
- unexpected Stage schema, grain, or key changes;
- corporate data or generated artifacts staged for Git;
- missing local prerequisite layers.

Acceptance criteria:

- required Stage files exist locally;
- selected Stage contract checks pass;
- differences are explained and reviewed;
- generated artifacts remain ignored.

Rollback notes: revert code/config changes under review and restore local generated artifacts from the approved local baseline or regenerate only after explicit approval.

## mart_contract_validation

Purpose: validate mart, slice, signal, and compact mart outputs against local Stage inputs.

What it proves:

- mart generation can run in the authorized local environment;
- accepted mart files and signal outputs are present;
- mart formulas, grains, and output contracts remain compatible with selected tests.

What it does not prove:

- final report rendering;
- live Ollama synthesis;
- public CI readiness.

Prerequisites:

- explicit task authorization;
- valid local `02_stage/01_full_stage.csv`;
- local `03_marts/`, `04_signals/`, and related artifact folders as needed.

Commands:

```bash
python3 src/build_marts.py
python3 -m unittest tests.test_mart_outputs -q
```

Expected outputs:

- production mart files under `03_marts/`;
- signal files under `04_signals/`;
- evidence and QA outputs where the mart builder produces them.

Allowed environment: authorized local machine only.

May write ignored artifacts: yes.

Stop rules:

- formula drift without approval;
- mart schema or grain changes without approval;
- missing expected mart/signal files;
- generated artifacts staged for Git.

Acceptance criteria:

- selected mart tests pass;
- accepted mart and signal files exist locally;
- material differences are reviewed against contracts.

Rollback notes: revert the change under review and restore/regenerate local marts only after explicit approval.

## report_artifact_validation

Purpose: validate local report package, evidence, chart, manifest, and release artifacts without changing business logic.

What it proves:

- local report package references expected files;
- accepted package checks can inspect generated artifacts;
- evidence, claim registry, chart manifests, and release manifests remain internally consistent when present.

What it does not prove:

- DOCX/PDF visual rendering unless render validation is also authorized;
- live Ollama quality unless `ollama_live_llm_validation` is also authorized;
- public clone readiness.

Prerequisites:

- explicit task authorization;
- local `04_charts/`, `05_evidence/`, `05_llm_package/`, `06_reports/`, and `07_qa/` artifacts as applicable;
- accepted package path and memo profile identified.

Commands:

```bash
python3 scripts/verify_accepted_ollama_report_packages.py
python3 scripts/validate_release_manifest.py
python3 scripts/check_no_release_on_fail.py
```

Expected outputs:

- validation pass/fail output;
- no committed generated artifacts;
- updated local QA files only when the authorized command is designed to write them.

Allowed environment: authorized local machine only.

May write ignored artifacts: possible, command-dependent.

Stop rules:

- missing accepted artifacts;
- release blocker in validation output;
- unsupported claim or evidence mismatch;
- generated artifacts staged for Git.

Acceptance criteria:

- selected artifact checks pass;
- skipped checks are documented;
- residual report risks are listed.

Rollback notes: revert source changes under review and keep local generated artifacts out of Git; regenerate only under an approved report task.

## render_docx_pdf_validation

Purpose: validate visual rendering, DOCX/PDF export, media presence, and final report package readability.

What it proves:

- DOCX/PDF/render tooling works locally;
- generated documents can be opened or rendered for QA;
- media and chart references are available in the local package.

What it does not prove:

- financial correctness without stage/mart validation;
- live LLM quality without Ollama validation;
- public clone readiness.

Prerequisites:

- explicit task authorization;
- local generated report package;
- local rendering toolchain such as LibreOffice when required;
- known accepted memo package folder.

Commands: task-specific render or visual QA commands only after approval.

Expected outputs:

- local rendered files, screenshots, QA reports, or export logs in ignored folders.

Allowed environment: authorized local machine only.

May write ignored artifacts: yes.

Stop rules:

- broken media references;
- render/export failure;
- visual QA failure;
- generated render artifacts staged for Git.

Acceptance criteria:

- selected render checks pass;
- final artifacts remain local/ignored;
- visible limitations and failures are documented.

Rollback notes: revert source/report changes and restore the previous accepted local package if needed.

## ollama_live_llm_validation

Purpose: validate live Ollama/LLM routing, generation, grounding, and downstream narrative QA in a local environment.

What it proves:

- local Ollama/live LLM service is reachable;
- approved generation path can run;
- generated narratives can be checked against evidence and QA gates.

What it does not prove:

- deterministic reproducibility across machines;
- financial correctness without deterministic inputs;
- public CI readiness.

Prerequisites:

- explicit task authorization;
- local Ollama/live LLM service;
- deterministic evidence and LLM package inputs;
- output folder and memo profile identified.

Commands: task-specific generation commands only after approval.

Expected outputs:

- local generated narratives, QA outputs, and package artifacts in ignored folders.

Allowed environment: authorized local machine only.

May write ignored artifacts: yes.

Stop rules:

- unsupported claims;
- invented numbers or causes;
- missing evidence;
- final judge or text QA failure;
- generated artifacts staged for Git.

Acceptance criteria:

- selected generation and QA checks pass;
- all material claims are evidence-backed;
- limitations and skipped checks are documented.

Rollback notes: discard generated local outputs or restore previous accepted report package; never commit generated LLM artifacts unless a separate approved task explicitly permits a safe text fixture.

## end_to_end_local_smoke

Purpose: run a bounded local smoke path across Stage, mart, artifact, and selected QA checks.

What it proves:

- the authorized local pipeline path can execute end-to-end for the selected scope;
- key local layers can be produced or validated together;
- selected contract and artifact checks pass in sequence.

What it does not prove:

- production readiness;
- every memo profile;
- every rendering or live LLM path unless separately included;
- public CI readiness.

Prerequisites:

- explicit task authorization;
- local ignored data and artifact layers;
- selected memo profile, period, and output scope;
- clear stop rules and rollback plan.

Commands:

```bash
python3 src/main.py
python3 src/build_marts.py
python3 -m unittest tests.test_output_contract -q
python3 -m unittest tests.test_mart_outputs -q
```

Additional report, render, or Ollama commands require separate explicit authorization.

Expected outputs:

- refreshed or validated local Stage, mart, signal, evidence, report, and QA artifacts for the selected scope.

Allowed environment: authorized local machine only.

May write ignored artifacts: yes.

Stop rules:

- any Stage/mart contract failure;
- reconciliation or formula drift;
- missing accepted artifacts;
- generated artifacts staged for Git;
- unauthorized report/render/Ollama execution.

Acceptance criteria:

- selected smoke path completes;
- selected tests/checks pass;
- differences are documented;
- generated outputs remain ignored.

Rollback notes: revert code/config changes under review and restore or regenerate local artifacts only under explicit approval.
