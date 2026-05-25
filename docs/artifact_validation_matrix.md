# Artifact Validation Matrix

These artifact folders are local/ignored and must not be committed. They require local data or generated artifacts and are not public-data-free.

| Group | Purpose | Local/Public Status | Expected Producer | Expected Consumer | Validation Command Or Future Need | Allowed In Git | May Be Regenerated | Risk If Stale | Risk If Accidentally Committed |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `01_raw/` | Corporate source workbooks and raw inputs. | Local only, ignored. | External/manual source delivery. | `src/main.py`. | Future input manifest and schema preflight. | No. | No, preserve raw inputs. | Pipeline reads outdated source data. | Corporate data exposure. |
| `02_stage/` | Cleaned Stage output and audit files. | Local only, ignored. | `src/main.py`. | `src/build_marts.py`, output contract tests. | `python3 -m unittest tests.test_output_contract -q` after authorization. | No. | Yes, with approval. | Mart layer built from stale Stage. | Corporate or derived data exposure. |
| `03_marts/` | Production marts, slices, compact marts, memo profile artifacts. | Local only, ignored. | `src/build_marts.py` and related builders. | signals, charts, reports, finance review. | `python3 -m unittest tests.test_mart_outputs -q` after authorization. | No. | Yes, with approval. | Reports use stale formulas or slices. | Derived financial data exposure. |
| `04_charts/` | Chart catalog, chart specs, chart data, chart images. | Local only, ignored. | chart package builders. | report generation and DOCX/short pack outputs. | Future chart manifest and media presence validation. | No. | Yes, with approval. | Broken or outdated charts in reports. | Derived chart/data exposure. |
| `04_signals/` | Signal tables and analytical signal outputs. | Local only, ignored. | `src/build_marts.py` and signal builders. | evidence, compact marts, memo packages. | Future signal catalog contract check. | No. | Yes, with approval. | Memo uses stale risk basis or signal classification. | Derived analytical exposure. |
| `05_evidence/` | Evidence cards and deterministic LLM context package. | Local only, ignored. | mart/evidence builders. | LLM package, memo generation, QA. | Future evidence registry and claim coverage check. | No. | Yes, with approval. | Claims may reference stale evidence. | Evidence and business finding exposure. |
| `05_llm_package/` | Deterministic memo inputs, claim candidates, evidence maps. | Local only, ignored. | memo data package builders. | Ollama/live LLM generation and report drafting. | Future package manifest and grounding preflight. | No. | Yes, with approval. | LLM generation uses stale context. | Memo input and claim exposure. |
| `06_reports/` | Report packages, DOCX/PDF/Excel, final memo outputs, source refs. | Local only, ignored. | report and depth-output builders. | management review, release QA. | `python3 scripts/verify_accepted_ollama_report_packages.py` after authorization. | No. | Yes, with approval. | Reviewers see stale or mismatched outputs. | Generated report exposure. |
| `07_qa/` | Cross-package QA, release, render, and validation artifacts. | Local only, ignored. | QA and release verification scripts. | release decision and rollback review. | Release/readiness scripts after authorization. | No. | Yes, with approval. | Release decision based on stale QA. | QA findings or business context exposure. |
| `99_archive/` | Archived or superseded local artifacts. | Local only, ignored. | manual/archive tasks. | rollback/reference only. | Future archive index and active/inactive labeling. | No. | No by default. | Confusion between active and archived artifacts. | Historical corporate data exposure. |

## Rules

- Do not add these folders to Git.
- Do not regenerate them unless the task explicitly authorizes local data-dependent execution.
- Do not use stale artifacts as acceptance evidence without stating their provenance.
- Do not copy artifact values into public issues, PRs, logs, or chat.
