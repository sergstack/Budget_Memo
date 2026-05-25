# Memo Task — Refund Impact Memo

## Status

planned

## Profile readiness

ready

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

How do player refunds affect fact, YoY, MoM and IN ratios?

## Audience

Уточняется по профилю. По умолчанию: Finance / CFO / COO / владельцы бюджета, если не указано иначе.

## Default depth mode

standard

## Business question

How do player refunds affect fact, YoY, MoM and IN ratios?

## Required source marts

- `03_marts/mart_main_full_budget.parquet`
- `03_marts/mart_signal_catalog_full.parquet`
- `03_marts/mart_flow_base_month.parquet`, если нужен IN / OUT / IN-OUT
- `03_marts/memo_profile_catalog.parquet`
- `03_marts/profile_readiness_matrix.parquet`

## Required slices

Определяются по readiness audit и текущему профилю. Все срезы должны идти от accepted MART / derived slices.


## Required blocks

- Refund rows.
- Refund amount.
- Refund share of fact.
- Refund impact by month.
- Refund impact by article.
- Refund impact by CFO.
- Refund impact by counterparty.

## Required charts

- Refund impact by month.
- Refund share by article/CFO.


## LLM / Ollama role

Ollama используется только для связного вывода:
- не считает метрики;
- не добавляет новые суммы;
- не придумывает причины;
- не скрывает ограничения;
- связывает утверждения на основе evidence.

## Stop conditions

- DQ Fail;
- нет grain;
- нет source mart;
- риск без risk_basis;
- action без owner / due date / status, если называется действием;
- IN ratios без valid denominator status;
- timing candidate назван confirmed timing;
- planning risk назван actual execution;
- Low Confidence подан как финальный факт.

## Expected outputs

Зависят от depth mode:
- short: короткий DOCX / графический pack;
- standard: управленческий DOCX;
- deep: Excel / evidence / QA package;
- action: action tracker XLSX.

## Acceptance criteria

- readiness audit выполнен;
- источники и срезы зафиксированы;
- графики имеют источник / метрику / grain / период / limitation;
- visible labels на русском;
- technical IDs только appendix / evidence;
- QA pass;
- no unsupported claims;
- no new calculations by LLM.


## Common forbidden actions

- Do not change Stage.
- Do not change raw files.
- Do not change MART formulas.
- Do not change accepted chart data.
- Do not build from raw/stage directly.
- Do not use old `final_memo.docx`.
- Do not write final outputs to root `06_reports/`.
- Do not claim production readiness.


## Next step

Выполнить Step 0 — Profile readiness audit.
