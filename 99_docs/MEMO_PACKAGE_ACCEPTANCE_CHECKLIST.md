# Memo Package Acceptance Checklist

Use this checklist before marking any memo package accepted.

## Source And Logic

- [ ] Inventory completed before generation.
- [ ] Logic review workbook exists when required by complexity, depth count, action mode, or analytical risk.
- [ ] Facts come only from accepted marts, accepted slices, evidence, or source_refs.
- [ ] Business formulas and schemas were not changed during final document generation.

## Charts

- [ ] Chart manifest exists.
- [ ] Chart manifest rows cover every chart used in final outputs.
- [ ] Chart limitations are non-empty.
- [ ] Chart PNG files exist.
- [ ] Chart sources, metrics, period, grain, filters, captions, and limitations are documented.

## Final Outputs

- [ ] Final DOCX exists for every required depth.
- [ ] Final MD exists where expected.
- [ ] Final XLSX exists where expected.
- [ ] No final outputs are created outside the canonical report folder.
- [ ] Deep workbook is not used as a substitute for a required deep DOCX when deep DOCX is in scope.

## DOCX Media And Render

- [ ] DOCX `word/media/` count meets the depth requirement.
- [ ] DOCX media count is not `0` when charts are required.
- [ ] LibreOffice render passes.
- [ ] Rendered PDF path is recorded in QA or release registry.

## QA Gates

- [ ] `text_qa` passes.
- [ ] `judge_preflight` passes.
- [ ] Final judge verdict is `accept`.
- [ ] Final judge is based on deterministic preflight facts.
- [ ] Business visual review is still required after technical acceptance.

## Actions

- [ ] Action mode is `candidate_only` unless externally confirmed fields exist.
- [ ] No fake owner is generated.
- [ ] No fake due date is generated.
- [ ] No fake action status is generated.
- [ ] No overdue chart or status funnel is generated without confirmed status/date evidence.

## Data/Mart Impact

- [ ] `02_stage/` mtime or hash check completed.
- [ ] `03_marts/` mtime or hash check completed.
- [ ] No stage/mart changes occurred during report generation.
- [ ] No schemas or formulas changed during release consolidation.

## Release

- [ ] Latest accepted QA folder is identified.
- [ ] Release registry updated.
- [ ] Residual risks documented.
- [ ] Next package recommendation documented.

## Factory Production Readiness

- [ ] Golden Memo Pack validation passed before claiming factory production readiness.
- [ ] Current `golden_memo_pack` status remains `active_candidate` and `production_ready=false` until real accepted golden case and negative-case stop tests pass.
- [ ] `config/memo_factory_quality_gates.yml` verified with `scripts/verify_memo_factory_quality_gates.py`.
- [ ] `config/memo_factory_routing_config.json` reviewed for required role/model metadata.
- [ ] Claim freeze verified with `scripts/verify_claim_freeze_for_release.py` before release.
- [ ] Release manifest validated with `scripts/validate_release_manifest.py`.
- [ ] High-risk release readiness checked with `scripts/verify_high_risk_release_readiness.py`.
