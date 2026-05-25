# Handoff to Codex

## Task type

implementation / QA

## Goal

Implement `golden_memo_pack` contract for analytical memo factory.

## Inputs

- `GOLDEN_MEMO_PACK_STANDARD.md`
- `README.md`
- `memo_template.md`
- `golden_case.contract.yml`
- `bad_cases.contract.yml`
- `judge_rubric.draft.yml`
- `claim_freeze_rules.yml`
- `acceptance_checklist.md`
- existing memo pipeline artifacts
- existing tests and schemas

## Expected output

- tests for positive golden case
- tests for bad cases
- claim freeze diff checker
- stop-rule checker
- judge_report schema validation
- release_manifest schema validation
- no-release-on-fail guard

## Constraints

- deterministic checks are code-first;
- LLM cannot add unfrozen claims;
- failed cases must not produce release artifact;
- no production-ready claim before acceptance;
- rubric weights are draft until calibrated on real memos.

## Acceptance criteria

- golden case passes only when all required artifacts exist;
- bad cases fail with expected stop-rules;
- release artifact is created only after QA pass;
- claim freeze diff blocks new claims, changed formulas, changed periods and fake evidence;
- acceptance checklist is generated or updated after run.

## Suggested first step

Create a minimal test harness that reads:

- `golden_case.contract.yml`
- `bad_cases.contract.yml`
- `claim_freeze_rules.yml`

Then emit:

- `golden_memo_pack_run_result.json`
- `failed_cases_result.json`
- `release_guard_result.json`
