# Memo Template

> Важно: это не golden memo. Это шаблон. Golden memo появляется только после реального accepted case.

# Аналитическая записка за {{period_or_report_date}}

## 1. Короткий вывод

За {{period_or_report_date}} ключевая картина выглядит так:

1. {{claim_001}}
2. {{claim_002}}
3. {{claim_003}}

Все выводы ниже должны быть подтверждены `evidence_id` из claim/evidence registry.

---

## 2. Что изменилось

| Блок | Вывод | Evidence |
|---|---|---|
| {{block_1}} | {{claim}} | {{evidence_id}} |
| {{block_2}} | {{claim}} | {{evidence_id}} |
| {{block_3}} | {{claim}} | {{evidence_id}} |

---

## 3. Финансовые / операционные показатели

| Метрика | Значение | Период | Evidence |
|---|---:|---|---|
| {{metric_1}} | {{value_1}} | {{period}} | {{evidence_id}} |
| {{metric_2}} | {{value_2}} | {{period}} | {{evidence_id}} |
| {{metric_3}} | {{value_3}} | {{period}} | {{evidence_id}} |

Правило: формула, период и сумма не могут быть изменены LLM. Все изменения только через deterministic formula/mart gate.

---

## 4. Риски

| Риск | Основание | Статус |
|---|---|---|
| {{risk_1}} | {{evidence_id}} | confirmed / candidate |
| {{risk_2}} | {{evidence_id}} | confirmed / candidate |

---

## 5. Действия

| Действие | Основание | Статус |
|---|---|---|
| {{action_1}} | {{evidence_id}} | candidate / approved |
| {{action_2}} | {{evidence_id}} | candidate / approved |

Правило: если нет owner/date/status из подтверждённого источника, действие остаётся candidate-only.

---

## 6. Что нельзя утверждать

- Нельзя утверждать причину отклонения без evidence.
- Нельзя назначать owner/date/status, если этого нет во внешнем источнике.
- Нельзя усиливать weak signal до confirmed issue.
- Нельзя менять формулы ради красивого вывода.
- Нельзя добавлять новый claim после claim freeze.

---

## 7. Release note

Записка может быть выпущена только если:

- all critical claims have evidence_id;
- formula checks passed;
- memo claims are subset of frozen claim_registry;
- judge verdict is pass or controlled warn;
- DOCX/render QA passed;
- release_manifest saved.
