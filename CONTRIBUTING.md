# Contributing

Budget_Memo is a financial analytics and memo-factory repository. Public GitHub work must preserve the separation between safe repository files and local corporate data or generated artifacts.

## Scope

Contributions should be small, reviewable, and tied to an explicit task. Prefer documentation, tests, safety tooling, and narrow fixes over broad rewrites.

Do not change business logic, formulas, schemas, output contracts, prompts, or QA gates unless the task explicitly approves that class of change.

## Public Vs Local Checks

Public data-free checks are safe in a fresh clone:

```bash
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

Full local pipeline checks require ignored corporate data and generated layers. Run them only when the task explicitly authorizes data-dependent validation.

Use the test profiles in `docs/test_strategy_matrix.md` and the CI policy in `docs/ci_matrix.md` when deciding which checks belong in a PR.

## Branch And PR Workflow

- Create a topic branch from `main`.
- Use focused branch names such as `docs/...`, `chore/...`, `fix/...`, or `test/...`.
- Keep each pull request limited to one objective.
- Fill out the PR template with checks run, skipped checks, risk, and rollback notes.
- Do not push directly to `main`.
- Do not force push unless repository maintainers explicitly approve it for the branch.

## Forbidden Actions Without Explicit Approval

- Running the full pipeline.
- Running report generation.
- Running Ollama or live LLM generation.
- Modifying ignored data, stage, mart, report, QA, archive, artifact, output, log, cache, or temp layers.
- Committing `.env`, keys, tokens, credentials, cookies, corporate workbooks, generated reports, or binary data artifacts.
- Changing formulas, schemas, contracts, prompts, memo doctrine, financial-control logic, or QA gates.

## Commit Expectations

Use concise commit messages that describe the change class:

```text
docs: clarify public clone checks
chore: add repository safety check
test: add data-free repo safety coverage
```

Avoid mixing documentation cleanup with business logic, schema, contract, or generated artifact changes.
