# Analytical Memo Visual Standard

## Purpose

This standard defines the deterministic visual QA layer for analytical memo DOCX/PDF outputs. It separates render correctness, visual layout quality, executive readability, and publishing hygiene from business logic QA.

The gate is diagnostic. It must not change report content, recalculate business formulas, alter metrics, rewrite conclusions, modify marts, modify prompts, or weaken existing QA gates.

## Status Verdicts

Every visual QA run reports these independent verdicts:

```yaml
docx_render_status: pass | revise | blocked
visual_layout_status: pass | revise | blocked
executive_readability_status: pass | revise | blocked
publishing_hygiene_status: pass | revise | blocked
overall_visual_release_status: pass | revise | blocked
```

- `pass`: no material defect was detected for the checked area.
- `revise`: the artifact renders, but release quality requires generator/style improvement.
- `blocked`: the artifact must not be released until the defect is fixed.

## Severity Matrix

| Defect | Severity |
|---|---|
| DOCX cannot render to PDF | blocker |
| PDF cannot render to PNG pages | blocker |
| Key table unreadable | blocker |
| Required chart missing | blocker |
| Required chart blank | blocker |
| Text clipped or outside page | blocker/high |
| Table outside margins | high |
| Main report and appendix mixed | high |
| Missing executive summary | high |
| Chart caption orphaned from chart | high |
| Required table missing | high |
| Tracked changes present | blocker |
| Comments present | blocker/high |
| Debug/local paths present | blocker/high |
| English technical chart titles in Russian report | medium/high |
| Inconsistent fonts or heading hierarchy | medium |
| Overdense page with no visual grouping | medium |
| Minor spacing/alignment inconsistency | low |

## Render Correctness vs Visual Quality

Render correctness checks whether a DOCX can be converted to PDF and PNG pages without producing a broken artifact. A render pass does not mean the memo is visually release-ready.

Visual quality checks whether the rendered pages are readable and professional: tables fit, charts are visible, captions stay near charts, pages are not overpacked, appendices are separated, and the first page supports executive scanning.

## Visual QA vs Business Logic QA

Visual QA does not validate financial formulas, mart transformations, risk scoring, or metric correctness. Those checks belong to data, mart, source reference, and business QA gates.

This task must not recalculate business formulas because recalculation belongs to controlled Python/SQL data validation and could mix report presentation with financial control logic. The visual gate may only flag obvious display inconsistencies, such as unreadable currencies, missing percentages, or broken table formatting.

## Deterministic Checks

The diagnostic gate should check:

- DOCX exists and is non-empty.
- DOCX package opens read-only.
- Comments and tracked changes are absent.
- Custom properties and metadata are not excessive.
- Debug paths, local temp paths, and embedded local file references are absent.
- LibreOffice or `soffice` can render DOCX to PDF.
- PDF pages can be rendered to PNG.
- Page count is greater than zero.
- Required media/charts are present and not blank where detectable.
- Tables and charts are represented in the rendered output.
- Release blockers are explicit.

## Heuristic or Manual Checks

Some checks are documented as heuristic/manual because deterministic image analysis cannot reliably prove them:

- clipped text;
- overlapping text;
- chart caption proximity;
- section heading orphaning;
- whether table wrapping is professionally readable;
- whether executive summary wording is sufficiently concise;
- whether main report and appendix feel cleanly separated.

The diagnostic script may emit `revise` findings for these areas when deterministic signals or visual review indicate risk.

## Release Logic

An artifact is release-ready only when:

- `overall_visual_release_status` is `pass`;
- `release_blockers` is empty;
- render, layout, executive readability, and publishing hygiene are all acceptable for the target audience.

Generator fixes must be performed in a separate implementation task. This standard only defines and runs the visual QA gate.

