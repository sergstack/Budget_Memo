# Performance And Refactor Gate

This gate applies before any performance optimization, refactor, pipeline change, report-generation change, or artifact-validation change. It is a planning and approval gate only; it does not authorize code changes.

## Required Before Work Starts

- [ ] Current behavior identified.
- [ ] Output contracts identified.
- [ ] A baseline command list is selected.
- [ ] Data-free checks pass.
- [ ] Local regression checks are selected if the change is data-dependent.
- [ ] Generated artifacts are not committed.
- [ ] Before/after comparison plan is documented.
- [ ] Rollback plan is documented.
- [ ] Explicit approval is recorded if formulas, schemas, output contracts, prompts, QA gates, or business logic are touched.

## Baseline Command Selection

Default public baseline:

```bash
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
python3 scripts/check_test_strategy.py
python3 -m unittest tests.test_test_strategy -q
```

Local data-dependent baselines must be selected from `docs/local_regression_plan.md` and must not run without explicit task authorization.

## Comparison Plan

Before changing code, define:

- input layers;
- output layers;
- selected periods;
- selected currencies;
- expected unchanged contracts;
- generated artifacts to compare;
- pass/fail threshold;
- reviewer responsible for acceptance.

Do not use LLM reasoning for numeric, financial, reconciliation, percentage, or variance comparisons. Use Python or SQL.

## Risk Classes

### low_risk_docs_or_checker_only

Examples:

- documentation clarification;
- data-free checker marker updates;
- CI governance text changes.

Expected validation:

- public data-free checks.

### medium_risk_pipeline_io

Examples:

- read/write path cleanup;
- reducing repeated Excel reads;
- caching local generated inputs;
- replacing repeated non-formula transformations.

Expected validation:

- public data-free checks;
- selected Stage/mart local regression checks;
- before/after artifact comparison.

### high_risk_formula_or_schema

Examples:

- formula changes;
- schema changes;
- output contract changes;
- row grain changes;
- financial-control logic changes.

Expected validation:

- explicit business approval;
- local regression plan;
- contract tests;
- before/after numeric reconciliation by Python or SQL.

### blocked_without_business_approval

Examples:

- changing formulas without approval;
- changing schemas or output contracts without approval;
- changing prompt doctrine or QA gates without approval;
- modifying raw inputs or accepted final artifacts without approval.

Expected validation:

- no implementation until approval and validation plan exist.

## Rollback

Default rollback is reverting the PR. If local artifacts were generated during an approved task, restore the previous accepted local artifact baseline or regenerate from unchanged inputs only after approval.
