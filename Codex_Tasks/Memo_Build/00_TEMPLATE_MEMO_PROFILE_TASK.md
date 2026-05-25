# Memo Task — <profile_code>

## Status

planned / active / blocked / preview_only

## Profile readiness

ready / partial / blocked / preview_only

## Step 0 — Profile readiness audit

Проверить до генерации любых финальных документов:

- [ ] профиль существует в `memo_profile_catalog`;
- [ ] нужные MART-файлы существуют;
- [ ] нужные срезы существуют;
- [ ] нужные графики существуют или могут быть построены из принятых срезов;
- [ ] нужный Excel-выход определён;
- [ ] evidence существует;
- [ ] QA status = pass / warning;
- [ ] stop conditions не блокируют публикацию.

Если readiness не `ready`, не создавать DOCX.

## Objective

Что должна ответить записка.

## Audience

Кто читает документ.

## Default depth mode

short / standard / deep / action

## Business question

Главный бизнес-вопрос.

## Required source marts

Список источников.

## Required slices

Список срезов.

## Required analytical blocks

Plan-Fact / YoY / MoM / Planning risk / IN context / DQ / Counterparties / Legal entities / Currency / Timing / Refunds / Actions.

## Required charts

Идеи графиков и источники срезов.

## Required Excel outputs

Slice workbook / appendix workbook / action tracker.

## LLM / Ollama role

Какой синтез нужен:
- короткий вывод;
- управленческий вывод;
- глубокий финансовый вывод;
- action-oriented вывод.

Default LLM chain:

```text
Ollama Analyst
→ source_registry.json
→ claim_evidence_matrix.json
→ judge_preflight_report.json
→ Ollama Judge
→ Russian Revisor
→ Final Judge / QA gate
```

Judge gate rules:
- FACT / CALCULATION require primary evidence.
- Numeric claims require `metric_ref`.
- Narrative drafts are `secondary_narrative` only and cannot be the only evidence for FACT / CALCULATION / executive claims / recommendation basis.
- Unsupported claims must be removed or moved to hypotheses / open questions before judge.
- Action wording remains candidate unless owner, due date and status are confirmed.
- Fallback judge is allowed only for invalid JSON/schema recovery, not for changing an unfavorable valid verdict.

## Stop conditions

Что блокирует публикацию.

## Expected outputs

DOCX / XLSX / MD / JSON / QA files.

## Acceptance criteria

Что должно пройти.

## Forbidden actions

Что нельзя менять.

## Next step

Первое действие Codex.
