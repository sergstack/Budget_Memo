# Documentation Consolidation Plan

This plan defines a safe path for future documentation cleanup. It does not delete, move, rename, or rewrite business content by itself.

## Goal

Reduce documentation duplication while preserving governance, auditability, handoff history, and business context.

## Scope

In scope for future docs-only tasks:

- ownership labels and canonical-source notes;
- short index pages;
- stale wording cleanup;
- archive labels for historical docs;
- duplicate-content consolidation after explicit review.

Out of scope:

- business logic changes;
- formulas, schemas, contracts, prompts, config, or output contract changes;
- moving active source files;
- deleting tracked files without a reviewed replacement;
- touching ignored local data, stage, mart, report, QA, archive, or artifact layers.

## Current Documentation Groups

Use `docs/documentation_map.md` as the current ownership map.

### Canonical Current Docs

Keep as current entrypoints:

- `README.md`
- `TESTING.md`
- `CONTRIBUTING.md`
- `CHANGELOG.md`
- `SECURITY.md`
- `AGENTS.md`
- `SPEC.md`
- `PROJECT_STATUS.md`
- `PROJECT_ARCHITECTURE_SUMMARY.md`
- `PROJECT_ARTIFACT_INVENTORY.md`
- `docs/developer_workflow.md`
- `docs/reviewer_quickstart.md`
- `docs/release_checklist.md`
- `docs/public_clone_smoke_check.md`
- `docs/repo_cleanup_policy.md`
- `docs/repo_governance.md`
- `docs/repo_hardening_audit.md`

### Active Planning Docs

Preserve until a separate planning-doc consolidation task defines a single owner:

- `PROJECT_MEMO_REGISTRY.md`
- `PROJECT_NEXT_MEMOS_PLAN.md`
- `PROJECT_DEPTH_MODES.md`
- `PROJECT_HANDOFF_NEXT_CHAT.md`

### Governance And Doctrine Docs

Do not delete without review:

- `99_docs/`
- `golden_memo_pack/`
- `99_docs/golden_memo_pack/`
- `docs/ANALYTICAL_MEMO_VISUAL_STANDARD.md`
- `docs/DOCX_VISUAL_QA_GATE.md`

### Task Package Backlog

Preserve as planning backlog until memo roadmap ownership is decided:

- `Codex_Tasks/Memo_Build/`

## Known Duplication

Known duplicate groups:

- `PROJECT_INSTRUCTIONS.md` and `99_docs/PROJECT_INSTRUCTIONS.md`.
- `golden_memo_pack/` and `99_docs/golden_memo_pack/`.
- Memo roadmap state across `PROJECT_MEMO_REGISTRY.md`, `PROJECT_NEXT_MEMOS_PLAN.md`, and `Codex_Tasks/Memo_Build/`.
- Project status and handoff context across `PROJECT_STATUS.md`, `PROJECT_HANDOFF_NEXT_CHAT.md`, `PROJECT_ARCHITECTURE_SUMMARY.md`, and `PROJECT_ARTIFACT_INVENTORY.md`.

Do not remove any duplicate until the canonical owner is chosen and the replacement path is documented.

## Consolidation Sequence

### Step 1: Label Ownership

Status: partially implemented.

Add short owner/status notes to duplicated documents:

- canonical current;
- historical handoff;
- governance doctrine;
- task package backlog;
- duplicate preserved pending review.

Allowed changes: docs-only labels and links.

Implemented labels:

- `PROJECT_INSTRUCTIONS.md`
- `99_docs/PROJECT_INSTRUCTIONS.md`
- `golden_memo_pack/README.md`
- `99_docs/golden_memo_pack/README.md`
- `Codex_Tasks/Memo_Build/README.md`

This is partial labeling only. Consolidation is not complete, and no deletion or moving has occurred.

### Step 2: Choose Canonical Owners

Decide the canonical owner for each duplicate group:

- project instruction owner;
- golden memo pack owner;
- memo roadmap owner;
- project status/handoff owner.

Output should be a reviewed decision note before any deletion or move.

### Stage 3 Governance / Developer Experience Docs

Status: added as current navigation and review aids.

Stage 3 adds contributor-facing governance and workflow documents plus GitHub PR/issue templates. These files clarify review expectations and safe public checks, but they do not complete documentation consolidation, delete duplicates, or replace business doctrine.

### Step 3: Add Cross-Links

Add cross-links from duplicates to canonical owners. Keep duplicated content intact during this phase.

### Step 4: Archive Labeling

For historical docs, add a visible label such as:

```text
Status: historical context; do not use as current source of truth without checking documentation_map.md.
```

Do not move files in this step.

### Step 5: Consolidation Proposal

Only after Steps 1-4, prepare a file-by-file proposal that classifies each candidate as:

- keep;
- merge into canonical owner;
- archive label only;
- delete candidate after explicit approval.

### Step 6: Execution In Small PRs

Execute only one consolidation group per PR. Each PR must:

- be docs-only;
- list exact files changed;
- avoid business logic and contracts;
- run data-free repo checks;
- avoid full pipeline, report generation, and Ollama.

## Do-Not-Touch List

Do not modify without explicit task approval:

- `src/`
- `scripts/` except repo-safety docs tooling tasks;
- `schemas/`
- `00_contracts/`
- `config/`
- `prompts/`
- `tests/fixtures/`
- data-dependent tests;
- ignored local data and artifact layers.

## Validation For Every Cleanup PR

Run:

```bash
git status --short
python3 scripts/check_repo_public_safety.py
python3 -m unittest tests.test_repo_public_safety -q
python3 scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

Do not run full pipeline, report generation, or Ollama unless explicitly authorized.

## Recommended Next Atomic Task

Add non-invasive ownership labels and cross-links to the first duplicate group:

- `PROJECT_INSTRUCTIONS.md`
- `99_docs/PROJECT_INSTRUCTIONS.md`

Do not delete either file in that task.
