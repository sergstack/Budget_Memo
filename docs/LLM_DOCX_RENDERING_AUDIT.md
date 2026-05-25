# LLM / DOCX Rendering Audit

Status: current inventory and safety note. This document does not implement the full renderer refactor.

## Rendering Entrypoints

| script/path | current role | writes final artifacts? | risk | recommended status |
| --- | --- | --- | --- | --- |
| `src/run_ollama_memo_pipeline.py` | Runs bounded Ollama memo pipeline, sanitization, judge flow, and package writes. | Can reference accepted final artifacts and write pipeline outputs, depending on caller inputs. | LLM/judge path is behavior-sensitive; must not bypass evidence or final QA. | `active` |
| `src/llm_revise_memo_narratives.py` | Runs LLM revisor pass over memo narratives. | No by default after this safety change; writes draft Markdown and QA JSON to selected output dir. | Previously could overwrite accepted final MD/DOCX directly. | `active_but_safety_limited` |
| `src/regenerate_clean_memo_narratives.py` | Regenerates clean deterministic final memo narratives and DOCX targets from accepted contracts. | Yes, writes configured final MD/DOCX targets. | Direct final writes; should be used only under explicit report-generation approval. | `needs_followup` |
| `src/build_docx_report.py` | Builds/polishes DOCX report package from accepted report inputs and visual standards. | Yes, writes DOCX/report outputs. | Appearance layer is complex and can diverge from canonical content. | `needs_followup` |
| `src/polish_docx_report.py` | Polishes memo 01 DOCX presentation and related QA outputs. | Yes, writes final/polished DOCX outputs. | Presentation-specific logic may bypass a canonical renderer contract. | `legacy_candidate` |
| `src/build_depth_mode_outputs.py` | Builds memo 01 depth outputs and related QA/inventory artifacts. | Yes, writes final depth artifacts. | Multi-output generator; should stay explicit-approval only. | `active` |
| `scripts/regenerate_memo01_memo02_ollama_factory.py` | Factory orchestration for memo01/memo02 Ollama generation, DOCX rendering, judges, and QA. | Yes, writes final MD/DOCX/XLSX and QA artifacts. | High-impact wrapper combining LLM, rendering, judges, and final writes. | `wrapper_candidate` |

## Safety Change

`src/llm_revise_memo_narratives.py` is safety-limited so the default revisor path is:

```text
LLM revisor -> draft Markdown + QA JSON only
```

Allowed default outputs:

```text
07_qa/...
06_reports/<memo>/draft/...
```

Forbidden default outputs:

```text
06_reports/<memo>/final/*.md
06_reports/<memo>/final/*.docx
```

The revisor records accepted final paths in QA metadata for traceability, but it does not write final MD/DOCX artifacts by default.

## Next Refactor Path

Future renderer stabilization should be handled as separate reviewed tasks:

```text
MemoDisplayContract -> canonical renderer -> visual QA gate -> release manifest
```

`src/memo_display_contract.py` now defines the standalone MemoDisplayContract v1 layer. It is not wired into DOCX rendering yet.

`src/memo_renderer.py` now defines a standalone canonical renderer v1 for synthetic/test MemoDisplayContract inputs. It is not wired into production generation yet.

`scripts/diagnose_docx_visual_quality.py` now defines a read-only DOCX visual QA gate v1. It writes diagnostics under the requested output folder and is not wired into release workflow yet.

Do not combine renderer consolidation with formula, schema, output-contract, prompt, QA-gate, or business-logic changes.
