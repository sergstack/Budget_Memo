# Golden Memo Pack

Назначение: regression/evaluation layer для фабрики аналитических записок.

Пакет проверяет:

1. good memo проходит gates;
2. bad memo останавливается;
3. unsupported claims не попадают в release;
4. формулы и периоды не меняются LLM;
5. release создаётся только после QA.

## Статус

```yaml
current_status: active_candidate
golden_status: blocked_until_real_case
production_ready: false
```

## Blocked до заполнения

- approved report_date / period;
- verified raw → stage → mart totals;
- accepted memo;
- claim_registry with evidence_id;
- expected judge_report;
- human acceptance note.

## Как использовать

1. Положить пакет в репозиторий фабрики аналитических записок.
2. Передать `HANDOFF_TO_CODEX.md` в Codex.
3. В `[Analytics]` выбрать реальный кейс/дату и подтвердить totals.
4. В `[LLM]` привязать prompt/rubric/judge к этим контрактам.
5. В `[Codex]` реализовать tests, claim freeze diff и no-release-on-fail guard.
