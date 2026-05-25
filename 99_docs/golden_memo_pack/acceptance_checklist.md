# Golden Memo Pack Acceptance Checklist

## A. Positive golden case

- [ ] selected real report_date / period
- [ ] raw source attached
- [ ] stage output attached
- [ ] mart output attached
- [ ] formula registry attached
- [ ] claim_registry attached
- [ ] all critical claims have evidence_id
- [ ] accepted memo attached
- [ ] expected judge_report attached
- [ ] human acceptance note attached

## B. Negative cases

- [ ] unsupported claim case fails
- [ ] formula change case fails
- [ ] new claim after freeze case fails
- [ ] generic action case warns/fails
- [ ] no release artifact created for failed cases

## C. Release conditions

- [ ] deterministic checks separated from LLM judges
- [ ] claim freeze diff implemented
- [ ] judge_report schema validated
- [ ] release_manifest schema validated
- [ ] DOCX/render QA automated
- [ ] human review enabled for high_risk

## Final status

```yaml
golden_memo_pack_status:
  allowed_values:
    - pass
    - fail
    - blocked

residual_risks:
  - TBD

next_scope:
  - TBD
```
