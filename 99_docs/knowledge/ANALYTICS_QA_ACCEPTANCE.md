# Analytics QA and Acceptance

## Acceptance checklist

An analytical package is accepted when:

- [ ] objective is clear;
- [ ] source data is identified;
- [ ] row grain is explicit;
- [ ] `stage_main_full` exists or exception is documented;
- [ ] `mart_main_full` exists or exception is documented;
- [ ] `mart_main_tz` / `mart_main_compact` exists or exception is documented;
- [ ] compact/TZ mart derives from `mart_main_full`;
- [ ] all slices derive from `mart_main_full`;
- [ ] formulas and metrics are explicit;
- [ ] totals reconcile where applicable;
- [ ] unsupported claims are visible;
- [ ] facts, hypotheses, and recommendations are separated;
- [ ] final conclusion is management-readable;
- [ ] limitations are listed.

## Smoke QA checklist

Use this for quick acceptance before sending a result or handoff:

```text
[ ] Inputs exist.
[ ] Main files standard checked.
[ ] stage_main_full checked.
[ ] mart_main_full checked.
[ ] mart_main_tz/compact checked.
[ ] Slices derive from mart_main_full.
[ ] No raw-to-conclusion shortcut.
[ ] No invented drivers.
[ ] No LLM text used as calculation source.
[ ] Key totals reconcile or blocker stated.
[ ] Risks/limitations stated.
[ ] Next step stated.
```

## Acceptance status format

```text
acceptance_status: pass / fail / blocked
checks_run:
files_or_objects_checked:
issues_found:
residual_risks:
next_step:
```

## Blocker format

```text
blocked_reason:
missing_input:
risk_if_continue:
safe_next_step:
files_inspected:
```
