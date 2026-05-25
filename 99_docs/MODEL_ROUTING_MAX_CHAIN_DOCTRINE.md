---
title: MODEL_ROUTING_MAX_CHAIN_DOCTRINE
architecture_standard: accepted
factory_default: true
production_status: accepted_factory_standard
scope: all analytical memo packages
runtime_enforcement: not_activated_in_this_documentation_update
---

# MODEL_ROUTING_MAX_CHAIN_DOCTRINE

Core rule:

```text
Code calculates.
LLM writes.
Judge cuts.
Release ships only proven artifacts.
```

This doctrine is the accepted factory standard for analytical memo packages.
It defines the default boundary between deterministic data work, LLM authoring, judge controls, and release acceptance.

## Default Boundary

- Data truth belongs to deterministic code, accepted marts, accepted slices, logic workbooks, evidence registries, and reproducible checks.
- Business meaning belongs to LLM authoring roles, constrained by accepted evidence and allowed claims.
- Evidence discipline belongs to judge and preflight gates.
- Release decisions belong to checklists, manifests, deterministic artifact checks, and human review where business risk requires it.

## Eight Quality Gates

1. Intake & Scope
2. Data Contract
3. Mart / Metric Verification
4. Evidence & Claim Registry
5. Analyst Lenses
6. Narrative & Writing
7. Judge & Revision
8. Artifact / Release / Learning

## Claim Freeze

After the Evidence & Claim Registry gate, LLM roles may rewrite wording, improve style, shorten text, and reorder blocks.
They must not add claims, add reasons, change amounts, change periods, change formulas, upgrade weak claims to strong claims, or invent evidence.

## Stop-Rules

Release must stop on:

- data contract failure;
- mart or metric verification failure;
- critical claim without evidence;
- formula or metric failure;
- evidence judge failure;
- DOCX media/render QA failure;
- release reviewer failure.

## Model Routing

Model routing is role-based. Each role must record:

- role;
- primary_model;
- fallback_model;
- fallback_used;
- fallback_reason;
- final_model;
- endpoint;
- response_status.

Routing configuration is documented in `config/memo_factory_routing_config.json`.
Quality gates are documented in `config/memo_factory_quality_gates.yml`.

## Release Rule

Technical acceptance is not business acceptance.
A memo is not releasable only because a DOCX exists, an LLM judge accepted it, or a deterministic script finished.
Release requires artifact checks, evidence traceability, render/media validation, release manifest or registry state, and human review for high-risk business acceptance.

## Memo-Specific Boundary

Scale the factory mechanism, not memo-specific findings.
Do not copy memo-specific content, metrics, business findings, or limitations between memos unless that memo's own evidence supports them.
