# Master Roadmap — фабрика аналитических записок

## Статус

Этот файл - главный маршрут для продолжения проекта.  
Он не является командой построить все записки сразу.

## Цель проекта

Создать управляемую фабрику аналитических записок:

```text
RAW
→ stage_main_full
→ mart_main_full
→ mart_main_compact
→ slices
→ signal catalog
→ memo profile
→ chart package
→ LLM / Ollama narrative candidate
→ source registry / claim evidence matrix / judge preflight
→ Ollama judge gate
→ DOCX / Excel
→ QA / acceptance
```

## Текущий статус

Первая записка-пилот завершена:

```text
memo_01 = executive_yoy_mom_budget_memo
```

Принято:
- Stage принят;
- MART пересобран и принят;
- 18 профилей записок созданы;
- governance профилей добавлен;
- графики построены и проверены;
- контракт записки создан;
- пакет данных для черновика создан;
- черновик создан;
- revised memo принят;
- DOCX создан;
- визуальная проверка DOCX пройдена;
- Ollama deep conclusion layer добавлен;
- Ollama judge gate настраивается как evidence-first: claim → source → evidence_level → confidence → section → verdict;
- production readiness не заявляется.

## Иерархия источников правды

```text
memo_profile_catalog = источник профилей записок
MART = источник расчётов
Codex_Tasks/Memo_Build/*.md = реализационные задачи
Word / Excel = выходные документы
```

## Общие источники

- `02_stage/01_full_stage.csv`
- `03_marts/mart_main_full_budget.parquet`
- `03_marts/mart_flow_base_month.parquet`
- `03_marts/mart_signal_catalog_full.parquet`
- `03_marts/mart_main_compact_executive_yoy_mom.parquet`
- `03_marts/memo_profile_catalog.parquet`
- `03_marts/profile_readiness_matrix.parquet`
- `04_charts/chart_catalog.xlsx`
- `05_llm_package/`
- `06_reports/`
- `07_qa/`

## Режимы глубины

### short

Короткая графическая executive-версия:
- 5-7 ключевых тезисов;
- 3-5 графиков;
- минимум текста;
- без тяжёлых evidence tables.

### standard

Стандартная управленческая записка:
- маршрут: Plan-Fact → YoY → MoM → localization → planning risk → IN context → QC;
- графики в теле;
- компактные ссылки на подтверждения.

### deep

Рабочий финансовый пакет:
- Excel со срезами;
- evidence map;
- методика и фильтры;
- QA / ограничения;
- source references;
- не длинная копия стандартной записки.

### action

Контур действий:
- действие;
- владелец;
- срок;
- статус;
- подтверждение;
- эскалация;
- следующий обзор.

## LLM / Ollama judge gate

Для всех LLM/Ollama-вариантов действует единый judge gate:

- перед full judge обязательны `source_registry.json`, `claim_evidence_matrix.json`, `judge_preflight_report.json`;
- evidence levels: `primary_metric`, `primary_table`, `primary_source_excerpt`, `secondary_narrative`, `unsupported`;
- FACT и CALCULATION claims проходят только с primary evidence;
- numeric claims требуют `metric_ref` на mart/table/evidence source;
- другой memo/draft/summary может быть только `secondary_narrative`, но не primary evidence;
- recommendations требуют supported FACT или INTERPRETATION basis;
- unsupported claims запрещены в executive summary, conclusions и recommendations;
- fallback judge разрешён только для invalid JSON/schema recovery и не может переигрывать валидный unfavorable verdict;
- финальный DOCX не создаётся из LLM-варианта без judge `accept` или явного human approval.

## Общие запреты

- не менять Stage;
- не менять raw files;
- не менять MART formulas;
- не менять принятые chart data;
- не строить из raw/stage напрямую;
- не использовать старый `final_memo.docx`;
- не писать финальные файлы в корень `06_reports/`;
- не заявлять production readiness;
- не позволять evidence appendix заменить executive memo.

## Общие правила проверки

- каждый вывод трассируется к MART / slice / evidence;
- каждый график имеет источник, метрику, период, зерно, фильтр, цель и ограничение;
- видимые подписи в отчетах и графиках на русском;
- technical IDs только в appendix / evidence / source_refs;
- риск имеет risk_basis;
- action имеет owner / due date / status, если называется действием;
- planning risk = future budget risk, not actual execution;
- timing candidate ≠ confirmed timing;
- IN ratios требуют валидный denominator status;
- ограничения видимы.

## Правило readiness-first

Каждая задача начинается с:

```text
Step 0 — Profile readiness audit
```

Если статус:
- `ready` - можно продолжать;
- `partial` - сделать missing-components plan, не делать DOCX;
- `blocked` - остановиться и написать blocker report;
- `preview_only` - только preview, без финального отчета.

## Приоритеты

### R0

1. `01_MEMO_01_DEPTH_CLEANUP.md`

### R1

2. `02_MONTHLY_PLAN_FACT_MEMO.md`
3. `03_PLANNING_RISK_MEMO.md`
4. `04_WEEKLY_COO_CASH_COST_MEMO.md`
5. `05_DATA_QUALITY_BLOCKER_MEMO.md`
6. `06_IN_OUT_PRESSURE_MEMO.md`

### R2

7. `07_ARTICLE_DEEP_DIVE_MEMO.md`
8. `08_CFO_OWNER_LOCALIZATION_MEMO.md`
9. `09_COUNTERPARTY_QUALITY_MEMO.md`
10. `10_QUARTERLY_BUDGET_DYNAMICS_REVIEW.md`
11. `11_SOURCE_MIX_RECONCILIATION_MEMO.md`
12. `12_CURRENCY_LEGAL_ENTITY_MEMO.md`

### R3

13. `13_TIMING_CANDIDATES_MEMO.md`
14. `14_REFUND_IMPACT_MEMO.md`
15. `15_COUNTERPARTY_CONCENTRATION_MEMO.md`
16. `16_FORECAST_RUN_RATE_MEMO.md`
17. `17_BUDGET_OWNER_ACTION_REGISTER_MEMO.md`
18. `18_BOARD_LEVEL_BUDGET_SUMMARY.md`

## Рекомендуемая первая задача

Начать с:

```text
Codex_Tasks/Memo_Build/01_MEMO_01_DEPTH_CLEANUP.md
```

Цель: привести смысл версий первой записки к принятой логике:
- `standard` = принятая управленческая записка;
- `short` = графический executive pack;
- `deep` = finance working package / slice workbook;
- `action` = action tracker.
