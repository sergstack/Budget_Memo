# Release Checklist

Use this checklist before merging a PR or preparing a tagged release. It is data-free by default and does not authorize full pipeline execution.

## Scope

- [ ] PR objective is clear.
- [ ] Files changed match the approved scope.
- [ ] No unrelated cleanup or formatting was included.
- [ ] Business logic, formulas, schemas, output contracts, prompts, and QA gates are unchanged unless explicitly approved.

## Data And Security

- [ ] No `.env` files are tracked.
- [ ] No secrets, credentials, keys, cookies, or tokens are included.
- [ ] No corporate data files are included.
- [ ] No generated reports, marts, QA artifacts, logs, caches, archives, or binary outputs are included.

## Data-Free Checks

Run:

```bash
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

Record pass/fail output in the PR.

## Test Profile

- [ ] PR states which test profile was used.
- [ ] PR states which test profiles were skipped and why.
- [ ] CI lane choice matches `docs/test_strategy_matrix.md` and `docs/ci_matrix.md`.

## Data-Dependent Checks

If not run, state why. Common safe reason:

```text
Skipped: task is docs-only/repo-hygiene and full local data pipeline was not authorized.
```

Only run full local checks when the task explicitly authorizes data-dependent validation.

## Generated Artifacts

- [ ] Generated artifacts remain in ignored local folders.
- [ ] No report outputs are committed.
- [ ] No QA/archive/output/log/cache folders are committed.

## Risks And Rollback

- [ ] Residual risks are listed.
- [ ] Rollback is documented as reverting the PR unless a more specific rollback is required.
- [ ] Next scope is identified separately from this release.
