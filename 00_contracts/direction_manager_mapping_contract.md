# CFO Owner Routing and Optional Direction Mapping Contract

Version: v0.2
Status: active_for_memo_02_internal_review
Scope: memo_02 monthly_plan_fact_memo; selected month `2026-04`
Updated: 2026-05-21

## Purpose

This contract defines owner routing and optional Direction mapping for memo_02.

Business decision: for memo_02, owner route is CFO. Separate Manager mapping is not required for release.

## Source of truth

Mapping and owner-route review inputs are maintained in:

`00_contracts/direction_manager_mapping_template.xlsx`

The template is a review/approval artifact. It does not modify raw, Stage or MART data by itself.

## Required sheets

1. `CFO_to_Direction` - optional analytical Direction grouping by CFO.
2. `CFO_to_Manager` - retained for governance history; Manager is `not_applicable` for memo_02.
3. `Article_to_Direction` - optional analytical Direction grouping by Article.
4. `Exceptions` - conflicts, exclusions, or override proposals.
5. `Memo_02_owner_route_summary` - CFO owner route coverage and release status support.

## Owner routing rules

- CFO is the owner route for memo_02.
- If `ЦФО` is populated, owner route is available.
- `Owner route = CFO` may be used for candidate action routing.
- Manager mapping is not required for memo_02.
- Direction mapping is optional analytical grouping and does not block memo_02 management release.
- Candidate action remains candidate until due date and status are confirmed.

## Final action rule

A final action may be published only when all conditions hold:

- owner route is available as CFO;
- due date is confirmed;
- action status is confirmed;
- the action claim is supported by evidence.

If due date or status is missing, action remains candidate even when CFO owner route exists.

## Direction mapping rules

Direction may be mapped from CFO or Article only through approved mapping rows, but Direction is optional for memo_02. Missing Direction must be disclosed as an analytical grouping limitation, not a release blocker.

Do not infer Direction directly from LLM narrative, counterparty, or old memo wording.

## Manager mapping rules

Manager mapping is `not_applicable` for memo_02. Do not invent managers. Do not treat `Кандидат владельца`, Article, Counterparty, or old memo text as confirmed Manager.

## Allowed mapping statuses

- `approved`: mapping is approved and may be used where applicable.
- `candidate`: proposed mapping; not confirmed.
- `rejected`: must not be used.
- `needs_review`: requires review.
- `not_applicable`: intentionally not applicable for memo_02.

## Memo 02 release rule

- If CFO owner route coverage is sufficient for priority rows and only due date/status are missing, memo_02 may move to `management_release_candidate_with_candidate_actions`.
- If CFO owner route is missing for material rows, status is `blocked_owner_route_missing`.
- Direction mapping does not block release.
- Manager mapping does not block release.
- Production readiness is not claimed by this contract.

## Forbidden actions

- Do not auto-fill Direction in MART.
- Do not change Stage/raw/MART formulas.
- Do not invent Manager.
- Do not publish final action-owner claims without due date and status.
- Do not regenerate memo_02 DOCX from this contract alone.
- Do not claim production readiness.

## QA requirements

- Manager mapping no longer blocks memo_02.
- CFO owner route is documented.
- Direction is optional.
- Action owner uses CFO.
- Final action remains blocked if due date/status are missing.
- No analytics outputs are changed unless separately approved.
