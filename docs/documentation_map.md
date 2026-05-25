# Documentation Map

This map explains current documentation ownership. It does not delete, move, or deprecate files by itself.

## canonical_current_docs

Current entrypoints for public reviewers and repository operators:

- `README.md`: public repository scope, project overview, safe public checks, local pipeline commands.
- `TESTING.md`: public data-free checks vs local data-dependent, report-generation, and Ollama-dependent checks.
- `CONTRIBUTING.md`: contributor scope, branch/PR workflow, forbidden actions, and safe check requirements.
- `CHANGELOG.md`: lightweight repository change history.
- `SECURITY.md`: public repository security policy and accidental exposure response.
- `AGENTS.md`: project guardrails for safe Codex work.
- `SPEC.md`: current stage and mart contracts, formulas, output contract notes, and risks.
- `PROJECT_STATUS.md`: current project status and residual risks.
- `PROJECT_ARCHITECTURE_SUMMARY.md`: layer architecture and accepted pipeline boundaries.
- `PROJECT_ARTIFACT_INVENTORY.md`: inventory of accepted local artifacts and ignored generated layers.
- `docs/developer_workflow.md`: public clone and local contributor workflow.
- `docs/reviewer_quickstart.md`: external reviewer orientation and safe commands.
- `docs/release_checklist.md`: PR/release readiness checklist.
- `docs/test_strategy_matrix.md`: test profile ownership and validation boundaries.
- `docs/ci_matrix.md`: CI lane policy and future CI expansion rules.
- `docs/public_clone_smoke_check.md`: public clone validation path.
- `docs/repo_cleanup_policy.md`: cleanup rules and deletion constraints.
- `docs/repo_governance.md`: repository governance, approval gates, and data/security rules.
- `docs/repo_hardening_audit.md`: repo hardening v1 audit.

## active_planning_docs

Planning documents that describe active or near-term memo work:

- `PROJECT_MEMO_REGISTRY.md`: memo profile registry, statuses, and priorities.
- `PROJECT_NEXT_MEMOS_PLAN.md`: next memo sequence and expected source slices/outputs.
- `PROJECT_DEPTH_MODES.md`: output depth modes and boundaries.
- `PROJECT_HANDOFF_NEXT_CHAT.md`: handoff context for continuing memo work.

These files may overlap, but they should be preserved until a separate planning-doc consolidation task defines a single owner for memo roadmap state.

## historical_handoff_docs

Useful historical context, lessons, and handoff material:

- `PROJECT_DECISIONS_AND_LESSONS.md`
- `docs/first_commit_candidate_review.md`
- `docs/github_publication_checklist.md`
- `99_docs/qa/SMOKE_QA_RESULT.md`

These files can be considered for future archive labeling, but should not be deleted without review because they preserve decision history and publication safety context.

## task_package_backlog_docs

Task packages and memo-build work packages:

- `Codex_Tasks/Memo_Build/00_MASTER_MEMO_ROADMAP.md`
- `Codex_Tasks/Memo_Build/00_TEMPLATE_MEMO_PROFILE_TASK.md`
- `Codex_Tasks/Memo_Build/README.md`
- `Codex_Tasks/Memo_Build/01_MEMO_01_DEPTH_CLEANUP.md` through `18_BOARD_LEVEL_BUDGET_SUMMARY.md`

These files are backlog/task design documents. They overlap with `PROJECT_MEMO_REGISTRY.md` and `PROJECT_NEXT_MEMOS_PLAN.md`, but remain useful until memo planning is consolidated. `Codex_Tasks/Memo_Build/README.md` labels the folder as task backlog and points to current public and roadmap entrypoints.

## governance_doctrine_docs

Governance, QA, release, and memo-factory doctrine:

- `99_docs/MEMO_FACTORY_DEFAULT_STANDARD.md`
- `99_docs/MEMO_FACTORY_KNOWN_REGRESSIONS.md`
- `99_docs/MEMO_FACTORY_RUNBOOK.md`
- `99_docs/MEMO_PACKAGE_ACCEPTANCE_CHECKLIST.md`
- `99_docs/MODEL_ROUTING_MAX_CHAIN_DOCTRINE.md`
- `99_docs/PROJECT_INSTRUCTIONS.md`
- `99_docs/knowledge/ANALYTICS_MAIN_FILES_STANDARD.md`
- `99_docs/knowledge/ANALYTICS_QA_ACCEPTANCE.md`
- `99_docs/knowledge/ANALYTICS_ROUTING_RULES.md`
- `golden_memo_pack/`
- `99_docs/golden_memo_pack/`
- `docs/ANALYTICAL_MEMO_VISUAL_STANDARD.md`
- `docs/DOCX_VISUAL_QA_GATE.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/`

Known duplicate: `PROJECT_INSTRUCTIONS.md` and `99_docs/PROJECT_INSTRUCTIONS.md` are intentionally preserved and now include ownership notes. Known duplicate: root `golden_memo_pack/` and `99_docs/golden_memo_pack/` are intentionally preserved and their README files now include ownership notes. Keep both copies until a separate consolidation task selects the canonical owner.

## do_not_delete_without_review

Do not delete these without explicit review and replacement:

- `SPEC.md`
- `AGENTS.md`
- `00_contracts/`
- `schemas/`
- `config/`
- `prompts/`
- `PROJECT_*.md`
- `99_docs/`
- `golden_memo_pack/`
- `Codex_Tasks/`
- `tests/fixtures/`

These files may contain contracts, governance rules, accepted decisions, test fixtures, or business context.

## future_consolidation_candidates

Candidates for later documentation-only consolidation:

- Choose one canonical owner for `PROJECT_INSTRUCTIONS.md` vs `99_docs/PROJECT_INSTRUCTIONS.md`.
- Choose one canonical owner for root `golden_memo_pack/` vs `99_docs/golden_memo_pack/`.
- Consolidate memo roadmap state across `PROJECT_MEMO_REGISTRY.md`, `PROJECT_NEXT_MEMOS_PLAN.md`, and `Codex_Tasks/Memo_Build/`.
- Add archive labels to historical handoff docs before considering deletion.

Stage 2.3-2.5 ownership labels have been added for the project-instructions duplicate group, the golden memo pack duplicate group, and the memo-build task backlog README. This is labeling only; no deletion, moving, or consolidation execution has occurred.

Stage 3 governance and developer-experience docs have been added as current navigation and review aids. They do not replace business doctrine, schemas, contracts, prompts, or historical handoff documents.

Any consolidation must be a separate reviewed task. Do not combine it with business logic, formula, schema, or output contract changes.
