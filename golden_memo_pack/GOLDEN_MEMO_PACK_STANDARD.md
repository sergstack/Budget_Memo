# GOLDEN_MEMO_PACK_STANDARD.md

## Статус

```text
status: active_candidate
type: golden_memo_pack_contract
production_ready: no
purpose: калибровка качества аналитических записок
```

Главное правило: это пока не golden memo, а контракт для сборки golden memo. Golden появится только после реальной accepted-записки, verified mart totals, judge pass и human acceptance.

---

## 1. Назначение

`golden_memo_pack` нужен для трёх вещей:

```text
1. Хорошая записка должна пройти все gates.
2. Плохая записка должна быть остановлена.
3. LLM не должна добавлять claims, которых нет в frozen claim registry.
```

Не цель:

```text
- не делать красивый шаблон ради шаблона;
- не плодить лишние файлы без acceptance;
- не считать placeholder golden example;
- не заменять human review.
```

---

## 2. Минимальная структура пакета

```text
golden_memo_pack/
├── README.md
├── memo_template.md
├── golden_case.contract.yml
├── bad_cases.contract.yml
├── judge_rubric.draft.yml
├── claim_freeze_rules.yml
├── acceptance_checklist.md
├── HANDOFF_TO_CODEX.md
└── MANIFEST.md
```

---

## 3. Acceptance principle

Пакет считается полезным только если:

1. positive golden case проходит все проверки;
2. negative bad cases останавливаются;
3. failed cases не создают release artifact;
4. critical claims без evidence_id блокируются;
5. formula/period changes блокируются;
6. new claims after freeze блокируются;
7. human review требуется для high-risk release.

---

## 4. Production readiness

Этот пакет не делает фабрику production-ready. Он создаёт evaluation / regression layer.

Production-ready статус возможен только после:

- approved real report_date / period;
- verified RAW → STAGE → MART totals;
- accepted memo;
- expected judge_report;
- human acceptance note;
- release_manifest;
- successful bad-case stop tests.
