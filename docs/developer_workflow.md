# Developer Workflow

This workflow is for public-clone contributors and local operators. It intentionally separates data-free repository checks from local data-dependent validation.

## Clone And Setup

```bash
git clone https://github.com/sergstack/Budget_Memo.git
cd Budget_Memo
python3 -m pip install -r requirements.txt
```

Do not expect corporate data, generated marts, reports, QA artifacts, DOCX/PDF outputs, or Ollama outputs to exist in a public clone.

## Public Data-Free Checks

Run these checks before opening a PR:

```bash
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

These checks do not prove the full financial pipeline. They only verify public repository safety and data-free configuration readiness.

For test-profile classification and CI policy, see `docs/test_strategy_matrix.md` and `docs/ci_matrix.md`.

## Local Data-Dependent Checks

The full pipeline and output-contract tests require ignored local layers such as `01_raw/`, `02_stage/`, `03_marts/`, `06_reports/`, and `07_qa/`.

Run data-dependent checks only when the task explicitly authorizes them. Do not run full report generation or Ollama/live LLM generation for docs-only, CI, or repo-hygiene work.

## Branch And PR Flow

1. Start from updated `main`.
2. Create a focused topic branch.
3. Make the smallest scoped change.
4. Run data-free checks.
5. Commit with a concise message.
6. Push the branch and open a PR.
7. Do not merge until review and CI are complete.

Recommended branch prefixes:

- `docs/`
- `chore/`
- `test/`
- `fix/`

## Commit Conventions

Use short imperative messages:

```text
docs: add reviewer quickstart
chore: update repo safety governance
test: cover public safety requirements
```

Avoid combining documentation cleanup with source changes, schema changes, formula changes, prompt changes, or generated artifact changes.

## Codex Task Package Expectations

Codex tasks should state:

- objective;
- allowed files;
- forbidden files and actions;
- checks to run;
- commit and PR rules;
- acceptance criteria;
- explicit approval if full pipeline, report generation, or Ollama is required.

## Review Guidance

Docs-only PRs should be reviewed for scope, stale wording, command accuracy, and consistency with `docs/documentation_map.md`.

Code, config, schema, contract, prompt, QA-gate, formula, or output-contract PRs require stricter review and task-specific approval.
