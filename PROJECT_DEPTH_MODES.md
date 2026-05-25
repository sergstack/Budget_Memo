# Project Depth Modes

Depth mode is a report-output parameter. It changes artifact depth and presentation form; it must not change Stage, MART formulas, chart data, or accepted analytics.

## Naming Convention

```text
<memo_number>__<memo_profile>__<depth_label>__<YYYY-MM-DD>__<status>.<ext>
```

Examples:

```text
01_executive_yoy_mom_budget_memo__short__2026-05-21__final.docx
01_executive_yoy_mom_budget_memo__standard__2026-05-21__final.docx
01_executive_yoy_mom_budget_memo__deep__2026-05-21__slices.xlsx
01_executive_yoy_mom_budget_memo__action__2026-05-21__final.xlsx
```

## short

Meaning: short executive chart-led pack.

Include:

- 5-7 key bullets.
- 3-5 key charts.
- Minimal text.
- Key risks and visible limitations.

Exclude:

- Heavy evidence tables.
- Full slice tables.
- Full appendix.
- Technical trace dump.

Rule: `short` is not a compressed full memo.

## standard

Meaning: accepted management memo.

Include:

- Route: Plan-Fact -> YoY -> MoM -> localization -> planning risk -> IN context -> QC.
- Charts in body.
- Compact evidence references.
- Visible limitations.

Exclude:

- Full technical evidence dump.
- Full working-package tables.

Rule: `standard` is the main management memo depth.

## deep

Meaning: finance working package.

Include:

- Full slice workbook.
- Evidence map.
- Method and filters.
- QA / limitations.
- Source references.
- DQ details.
- IN/OUT checks.
- Planning risk details.
- Counterparty / currency / legal entity appendix slices.

Exclude:

- Decorative executive prose.
- Duplicate long memo unless explicitly required.

Rule: `deep` is a working package, not a duplicate long memo.

## action

Meaning: operating action tracker.

Include:

- Signal.
- Object.
- What to check.
- Owner.
- Due date.
- Status.
- Confirmation.
- Escalation.
- Evidence ID.
- Next review date.

Exclude:

- Narrative memo body.
- Unsupported recommendations.

Rule: `action` is a tracker, not narrative memo.
