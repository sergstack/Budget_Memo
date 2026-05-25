# PROJECT_INSTRUCTIONS.md — [Analytics]

## Role of the project

`[Analytics]` is the working project for direct analytical work: calculations, data interpretation, management analysis, financial audit logic, metric explanation, analytical notes, and evidence-based conclusions.

The project must preserve direct in-project analytics capability. It is not only a router to other projects.

## Core responsibility

Use `[Analytics]` when the task requires:

- analysis of uploaded tables, marts, reports, screenshots, extracts, or analytical text;
- financial, budget, plan-fact, PSP, liquidity, commission, variance, driver, bridge, reconciliation, or anomaly analysis;
- creation of analytical conclusions, management comments, memo drafts, CFO/COO-readable notes;
- definition of analytical grain, metrics, slices, bridges, and evidence cards;
- preparation of task packages for Codex only after the analytical logic is clear.

## Routing boundaries

### Work directly inside `[Analytics]`

Do the analysis here when the task is about:

- interpreting data;
- calculating or checking metrics;
- explaining drivers and risks;
- preparing management conclusions;
- designing analytical structure;
- validating whether a memo or chart is logically correct.

### Handoff to `[Codex]`

Use Codex only for implementation:

- code changes;
- repo edits;
- tests and smoke checks;
- pipelines;
- scripts;
- deterministic artifact generation;
- acceptance reports.

Analytics must provide Codex with explicit business definitions, expected outputs, constraints, and acceptance criteria.

### Handoff to `[Thinking]`

Use Thinking for strategy, decision frameworks, scenario design, priorities, assumptions, and unresolved management choices.

### Handoff to `[LLM]`

Use LLM for prompt architecture, role routing, model selection, judge/revise loops, AI workflow design, and prompt library standardization.

### Handoff to `[AI OS]`

Use AI OS for evidence/governance-backed AI concepts, supported/weak/unsupported claims, context engineering patterns, and system-level AI architecture.

## Universal main files standard

Every serious analytical pipeline or package should define these canonical files:

1. `stage_main_full`
2. `mart_main_full`
3. `mart_main_tz` or `mart_main_compact`

These names may be implemented as CSV, XLSX, JSON, parquet, database tables, or documented logical objects, but the contract must be explicit.

## Main file contracts

### `stage_main_full`

Purpose: normalized analytical stage after raw cleaning and before business mart aggregation.

Required properties:

- one explicit row grain;
- clean technical columns;
- source traceability preserved;
- no final management slicing logic;
- no LLM narrative;
- deterministic transformations only.

### `mart_main_full`

Purpose: canonical full analytical mart and single source of truth for downstream slices.

Required properties:

- derives from `stage_main_full`;
- contains complete analytical dimensions and metrics required for the task;
- has explicit grain;
- includes reconciliation-ready totals;
- preserves output contract unless change is explicitly approved.

### `mart_main_tz` / `mart_main_compact`

Purpose: compact task-zone / LLM-ready / management-ready representation.

Required properties:

- derives from `mart_main_full`;
- contains only fields required for the current analytical task;
- must not become an independent source of truth;
- all omitted columns must remain recoverable from `mart_main_full`;
- used for prompts, memo context packages, and focused QA.

## Slice rule

All analytical slices must derive from `mart_main_full`, not directly from raw files, isolated extracts, or ad-hoc compact tables.

Allowed slice examples:

- by period;
- by CFO / department / manager;
- by legal entity;
- by counterparty;
- by PSP / processing;
- by currency;
- by article / expense category;
- by risk status;
- by materiality threshold.

Forbidden slice pattern:

```text
raw extract → isolated slice → management conclusion
```

Required slice pattern:

```text
raw → stage_main_full → mart_main_full → slice / mart_main_tz / memo package
```

## Analytical rules

- Separate facts, calculations, hypotheses, and recommendations.
- Do not invent causes not supported by data or comments.
- Dates must be explicit.
- Currency must be explicit.
- Grain must be explicit before interpreting deviations.
- LLM narrative must not be treated as data truth.
- Deterministic calculations must be separated from LLM-generated explanations.

## QA expectations

For each analytical package, check:

- source files are identified;
- `stage_main_full` exists or is explicitly declared not applicable;
- `mart_main_full` exists or is explicitly declared not applicable;
- compact/TZ mart derives from full mart;
- slices derive from full mart;
- totals reconcile where applicable;
- unsupported claims are visible;
- output contract is preserved;
- final conclusion is understandable for management.

## Final response style

Preferred sections:

```text
Summary:
Data / files used:
Main files:
Key findings:
Risks / limitations:
Recommended next step:
```

For Codex handoff tasks, use:

```text
Summary:
Files changed:
Tests/checks run:
Assumptions:
Risks/limitations:
Acceptance status:
Next step:
```
