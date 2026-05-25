# Repository Governance

Budget_Memo is maintained as a public-safe repository with local-only corporate data and generated artifacts. Governance exists to preserve financial logic, contracts, and reproducibility while allowing safe documentation, tests, and tooling improvements.

## Roles And Ownership

- `README.md`: public entrypoint and high-level project overview.
- `TESTING.md`: test classes and safe command boundaries.
- `docs/documentation_map.md`: documentation ownership map.
- `docs/documentation_consolidation_plan.md`: future docs cleanup plan.
- `docs/reviewer_quickstart.md`: external reviewer orientation.
- `docs/developer_workflow.md`: contributor workflow.
- `docs/release_checklist.md`: PR and release readiness checklist.
- `AGENTS.md`: project rules for Codex work.
- `SPEC.md`, `00_contracts/`, `schemas/`, `config/`, and `prompts/`: contract and doctrine-sensitive materials.

## Source Of Truth

Use current docs before historical or backlog docs:

1. `README.md`
2. `PROJECT_STATUS.md`
3. `PROJECT_ARCHITECTURE_SUMMARY.md`
4. `TESTING.md`
5. `docs/documentation_map.md`
6. `docs/repo_governance.md`

Historical handoff docs, task packages, and duplicate doctrine packs are preserved for context until a reviewed consolidation task changes ownership.

## Forbidden Change Classes Without Approval

Do not change these without explicit task approval:

- business logic;
- formulas;
- schemas;
- output contracts;
- prompt doctrine;
- QA gates;
- financial-control logic;
- raw/stage/mart/report layer semantics;
- generated report artifacts;
- ignored local data and artifact folders.

## Approval Gates

Docs-only and repo-hygiene changes may use public data-free checks.

Changes touching source code, contracts, schemas, config, prompts, data-dependent tests, or output contracts require task-specific approval and validation planning.

Full pipeline, report generation, and Ollama/live LLM generation require explicit approval before execution.

## Documentation Consolidation Policy

Documentation consolidation must happen in small PRs. Label ownership first, add cross-links second, and only propose deletion after a reviewed replacement path exists.

Do not delete or move `PROJECT_*.md`, `99_docs/`, `golden_memo_pack/`, or `Codex_Tasks/` without a separate approved task.

## Branch And PR Policy

- Work on topic branches.
- Do not push directly to `main`.
- Do not force push unless explicitly approved.
- Use the PR template.
- List checks run and checks skipped.
- Keep each PR focused on one objective.

## Data And Security

Corporate data, generated artifacts, secrets, credentials, keys, cookies, private configs, and local outputs must stay out of Git.

Run the public safety check before PR:

```bash
python3 scripts/check_repo_public_safety.py
```
