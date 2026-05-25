# Project Decisions And Lessons

## Decisions Accepted

- Stage is accepted as `stage_main_full` analogue: `02_stage/01_full_stage.csv`.
- MART is the layer for formulas, metrics, classifications, risk basis, and rankings.
- Executive memo content uses compact MART and signal catalog.
- Evidence and detailed slices remain available in full MART, slice workbooks, and evidence maps.
- First memo profile completed: `executive_yoy_mom_budget_memo`.
- Active report folder for memo 01 is profile-named: `06_reports/01_executive_yoy_mom_budget_memo/`.
- Active report inventory is `06_reports/_inventory/report_inventory.md`.
- Depth labels are `short`, `standard`, `deep`, and `action`.
- Ollama may synthesize narrative conclusions only from accepted deterministic evidence.

## Mistakes Found

- Early downstream artifacts mixed concerns from MART onward.
- A legal entity / currency Excel sheet mixed two grains.
- Some Excel-visible labels were English technical values.
- IN ratios appeared where denominator period/scope was not clearly valid.
- Evidence strings overloaded the executive memo body.
- Initial depth output folder `memo_01/` was too abstract.
- Initial `short` behaved like a compressed memo instead of a chart-led pack.
- Initial `deep` behaved like a repeated memo with appendix instead of a finance working package.

## Corrections Made

- Old downstream layer archived before MART rebuild.
- MART rebuilt from accepted Stage.
- Legal entity and currency sheets split by grain.
- Russian business-readable chart/report labels added.
- Chart package polished with muted executive palette.
- Evidence detail moved toward appendix/source refs.
- Report folder restored to profile-named active folder.
- Generic `memo_01/` and inactive `99_inventory/` archived.
- Active inventory restored to `_inventory`.

## Rules To Prevent Recurrence

- Do not build Word directly from raw/stage.
- One Excel sheet = one grain.
- No English technical labels in executive-facing outputs.
- No mixed legal/currency sheet.
- IN ratios require valid denominator period/scope.
- Timing candidate is not confirmed timing.
- Planning risk is future risk, not execution.
- Evidence tables should not overload executive body.
- `short` is chart-led, not a compressed full memo.
- `deep` is finance working package, not a duplicate long memo.
- `action` is tracker, not narrative memo.
- Ollama is narrative synthesis, not calculation source.
- Risk requires `risk_basis`.
- Low confidence must not be written as final fact.
- Recommendations require owner / due date / status where available.
