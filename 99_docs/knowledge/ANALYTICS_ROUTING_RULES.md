# Analytics Routing Rules

## Default rule

`[Analytics]` performs analysis directly.

Do not hand off analytical thinking by default. Handoff is needed only when the task belongs to implementation, strategy, prompt orchestration, or AI evidence governance.

## Route matrix

| User intent | Stay in Analytics | Handoff |
|---|---:|---|
| Analyze numbers / deviations / drivers | yes | no |
| Explain chart or memo logic | yes | no |
| Build CFO/COO conclusion | yes | no |
| Define metric / grain / slice | yes | no, unless implementation needed |
| Write Codex task package | yes, as preparation | to Codex after package is ready |
| Modify repo / scripts / tests | no | Codex |
| Design model routing / prompts | no | LLM |
| Decide strategy / priorities | no | Thinking |
| Verify AI concept with KB evidence | no | AI OS |

## Handoff trigger to Codex

Send to Codex when the expected output includes:

- changed code;
- changed repository docs;
- tests;
- smoke checks;
- generated deterministic artifacts;
- pipeline implementation;
- release/rollback report.

## Required Codex handoff fields

```markdown
# Codex Task

## Context
## Objective
## Inputs
## Files to inspect
## Files allowed to modify
## Forbidden actions
## Expected outputs
## Acceptance criteria
## Tests / smoke checks
## Rollback plan
## Final response format
```

## Forbidden routing mistake

Do not send to Codex a vague task like:

```text
Improve the analytical memo.
```

Correct pattern:

```text
Implement deterministic validation that checks whether final_memo.docx contains required sections A/B/C and whether all claims map to evidence IDs from mart_main_full-derived context package.
```
