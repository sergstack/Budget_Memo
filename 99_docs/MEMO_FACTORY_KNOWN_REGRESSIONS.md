# Memo Factory Known Regressions

Track these regressions explicitly during future memo package work.

| Regression | Why It Blocks Release | Required Control |
|---|---|---|
| QA-safe skeleton outputs | They look complete but are not business-accepted memo packages. | Require inventory, logic workbook when needed, chart manifest, embedded media, render, and judges. |
| Final DOCX with 0 embedded media | DOCX existence alone does not prove charts are present. | Inspect `word/media/` with `zipfile` and enforce depth media minimums. |
| Chart manifest with empty limitation | Charts without limitations can support unsupported conclusions. | Fail manifest completeness when any limitation is empty. |
| Final judge contradicting deterministic preflight | LLM judgment cannot override observed files and checks. | Feed deterministic preflight summary and block contradictions. |
| Technical IDs leaking into executive body | Executive outputs become unreadable and expose implementation detail. | Keep IDs in appendices, manifests, workbooks, or evidence tables unless needed. |
| Evidence cards dumped inline into narrative | Narrative becomes an evidence dump rather than an analytical memo. | Summarize claims in memo; keep evidence cards in source_refs/workbooks. |
| LLM generating confirmed actions without owner/due/status | Creates false commitments and fake operating controls. | Default action mode to `candidate_only`; require external confirmation for owner/date/status. |
| Old/stale QA artifacts treated as latest | Release can cite obsolete checks. | Registry must identify latest accepted QA path and status source. |
| Missing action DOCX in delivery list despite accepted matrix | A package can appear accepted while one depth is absent from delivery. | Explicit per-depth output matrix and direct action DOCX existence check. |
| Local Python missing optional dependency like `tabulate` | Generation/QA scripts can fail after partial writes. | Avoid optional dependency assumptions or provide deterministic fallback. |
| LibreOffice not found in PATH but available at macOS app path | Render can be falsely reported blocked. | Check `/Applications/LibreOffice.app/Contents/MacOS/soffice` before blocking render. |
| Doctrine quality gates config missing or stale | Stop-rules become tribal knowledge instead of an executable release contract. | Verify `config/memo_factory_quality_gates.yml` with `scripts/verify_memo_factory_quality_gates.py`. |
| Claim-freeze diff skipped before release | LLM/revisor can add claims after evidence freeze. | Run `scripts/verify_claim_freeze_for_release.py` before release. |
| Release manifest accepted without required QA paths | Release status can say pass while judge/render/human-review artifacts are absent. | Validate manifests with `scripts/validate_release_manifest.py`. |
| High-risk memo released without human review state | Technical gates can be mistaken for high-risk business acceptance. | Run `scripts/verify_high_risk_release_readiness.py` and record human review as complete or pending. |
