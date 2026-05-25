# Memo Factory Default Standard

## Default Rule

`MODEL_ROUTING_MAX_CHAIN_DOCTRINE` is the default standard for all analytical memo tasks.
Future prompts do not need to repeat this doctrine; Codex must assume it by default for analytical memo work unless explicitly overridden.

## What Applies To Every Memo

- Code calculates.
- LLM writes.
- Judge cuts.
- Release ships only proven artifacts.
- Evidence, media, render, claim-freeze, and release checks remain mandatory.

## What Remains Memo-Specific

Each memo keeps its own metrics, slices, formulas, limitations, action rules, and business questions.
Do not copy memo-specific content between memos.
Scale the factory mechanism, not memo-specific findings.

## Deterministic vs LLM Boundary

Deterministic layers own facts, numbers, formulas, tables, charts, evidence registries, source references, and artifact assembly.
LLM roles own management interpretation and narrative rewriting under evidence constraints.

## Eight Quality Gates

1. Intake & Scope
2. Data Contract
3. Mart / Metric Verification
4. Evidence & Claim Registry
5. Analyst Lenses
6. Narrative & Writing
7. Judge & Revision
8. Artifact / Release / Learning

## Stop-Rules

Stop on failed data contract, failed mart/metric verification, critical claims without evidence, formula/metric failure, evidence judge failure, DOCX media/render failure, or release reviewer failure.

## Claim Freeze

After the evidence and claim registry is frozen, LLM roles may improve wording and structure only.
They must not add claims, reasons, amounts, periods, formulas, stronger certainty, or invented evidence.

## Release Rule

Technical acceptance, evidence acceptance, language acceptance, visual acceptance, business acceptance, and release acceptance are separate states.
High-risk business acceptance requires human review.

## Out Of Scope For Normal Memo Generation

Normal memo generation must not rebuild marts, change schemas, change formulas, modify raw/stage layers, weaken QA gates, or activate runtime enforcement beyond the approved factory configuration.
