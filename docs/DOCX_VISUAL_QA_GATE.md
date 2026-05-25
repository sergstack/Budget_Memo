# DOCX Visual QA Gate

## Purpose

The DOCX visual QA gate is a read-only diagnostic command for analytical memo DOCX/PDF outputs. It produces separate verdicts for:

```yaml
docx_render_status: pass | revise | blocked
visual_layout_status: pass | revise | blocked
executive_readability_status: pass | revise | blocked
publishing_hygiene_status: pass | revise | blocked
overall_visual_release_status: pass | revise | blocked
```

The gate must not modify the source DOCX, business calculations, marts, schemas, prompts, report conclusions, or existing QA thresholds. It does not run live Kestra and does not require scheduler access.

## How To Run

```bash
python3 scripts/diagnose_docx_visual_quality.py \
  --docx path/to/report.docx \
  --out artifacts/diagnostics/docx_visual_YYYYMMDD_HHMMSS/
```

The command is read-only against `--docx`. Diagnostic artifacts are written only under `--out`.

## Expected Artifacts

```text
diagnostic_report.md
defects.json
rendered.pdf
pages/
  page_001.png
  page_002.png
logs/
  libreoffice_stdout.log
  libreoffice_stderr.log
  pdf_render_stdout.log
  pdf_render_stderr.log
```

## What Is Checked Deterministically

- target DOCX exists and is non-empty;
- DOCX package is readable;
- embedded media count;
- comments and tracked changes;
- custom properties;
- local/debug/temp paths;
- LibreOffice/`soffice` availability;
- DOCX to PDF render;
- PDF to PNG page render;
- page count greater than zero;
- blank or near-blank pages by raster signal;
- JSON and Markdown report creation.

## What Is Reported As Heuristic Review

The gate documents risks that require visual or generator review:

- chart caption separated from chart;
- long tables that fit technically but are hard to read;
- technical English titles in Russian reports;
- main report and appendix mixed together;
- weak first page or missing executive summary;
- over-dense pages or excessive whitespace.

## Severity Matrix

| Severity | Meaning |
|---|---|
| blocker | Must not release. Rendering, publishing hygiene, or required artifact is broken. |
| high | Must fix before normal release. The memo may render but is not professional or readable. |
| medium | Should fix soon. Quality/readability risk exists. |
| low | Cosmetic or minor consistency issue. |

## Status Meanings

- `pass`: no material defect detected.
- `revise`: artifact renders but should be improved.
- `blocked`: release is blocked.

## Release Decision

The gate exits non-zero if any `blocker` defect is found. A `revise` verdict means the DOCX can be inspected, but generator/style improvements are still needed before regular business release.

## Business Logic Boundary

This gate explicitly prohibits business logic changes. It does not recalculate totals, deltas, percentages, risk scores, mart outputs, or financial formulas. Any financial or analytical validation must remain in Python/SQL data QA and source reference QA.

## Generator Fix Boundary

If the gate finds visual defects, the next task should revise the DOCX/report generator. The diagnostic command itself must not auto-fix DOCX files, rewrite memo text, hide risks, or alter evidence markers.

