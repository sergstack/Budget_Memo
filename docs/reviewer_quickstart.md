# Reviewer Quickstart

Budget_Memo is a public-safe financial analytics and memo-factory repository. Corporate data and generated artifacts are intentionally absent from Git.

## What Is In The Public Repo

- Source code.
- Contracts, schemas, config, prompts, and tests.
- Documentation, governance, and safety tooling.
- Data-free CI and repository smoke checks.

## What Is Intentionally Missing

- Corporate source workbooks.
- Stage and mart outputs.
- Chart packages and signal outputs.
- Evidence and LLM packages.
- Final reports, DOCX/PDF/Excel artifacts, QA outputs, logs, caches, and archives.
- `.env`, credentials, keys, tokens, cookies, and private configs.

## Safe Commands

Run these in a public clone:

```bash
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

## Do Not Run From A Public Clone

- Full pipeline execution.
- Report generation.
- Ollama or live LLM generation.
- Data-dependent mart, stage, accepted-package, render, or output-contract validation unless local ignored artifacts are present and the task authorizes it.

## How To Interpret CI

`Repo Smoke` validates repository safety and data-free configuration readiness. It does not prove the full local financial pipeline, report generation, DOCX/PDF rendering, or Ollama synthesis.

## Where To Start

- `README.md`: project overview and public scope.
- `TESTING.md`: test classes and safe commands.
- `docs/developer_workflow.md`: contribution workflow.
- `docs/repo_governance.md`: governance and approval gates.
- `docs/documentation_map.md`: documentation ownership map.
- `docs/documentation_consolidation_plan.md`: future documentation cleanup plan.
