# Testing

## Public Data-Free Checks

These checks are safe for a public clone and do not require corporate workbooks, generated marts, report artifacts, Ollama, or LibreOffice:

```bash
python scripts/check_repo_public_safety.py
python -m unittest tests.test_repo_public_safety -q
python scripts/verify_memo_factory_quality_gates.py --config config/memo_factory_quality_gates.yml
```

GitHub Actions must stay limited to this data-free class of checks.

For the full test-profile policy and CI lane policy, see:

- [Test strategy matrix](docs/test_strategy_matrix.md)
- [CI matrix](docs/ci_matrix.md)

For public review and contribution workflow context, see:

- [Reviewer quickstart](docs/reviewer_quickstart.md)
- [Developer workflow](docs/developer_workflow.md)

## Run All Unit Tests

```bash
python3 -m unittest discover -s tests -q
```

This is the local full unit test command. Some tests may require ignored local data, generated artifacts, or local QA fixtures and are not suitable for public GitHub CI unless explicitly classified as data-free.
It is local validation and not the default public CI command.

## Run Selected Tests

Run one test module:

```bash
python3 -m unittest tests.test_output_contract -q
```

Run pytest-based contract tests when `pytest` is available:

```bash
python3 -m pytest tests/test_golden_memo_pack_contract.py -q
python3 -m pytest tests/test_memo_factory_doctrine_enforcement.py -q
```

## Ollama-Dependent Tests

Tests that exercise `src.run_ollama_memo_pipeline` or live memo generation may require a reachable Ollama endpoint.
Skipped Ollama tests mean the local model service was unavailable; they are not evidence that generation passed.

Do not run memo generation tests or live report pipelines unless the task explicitly asks for regeneration.

## Local Data-Dependent Checks

These checks require ignored local layers such as `01_raw/`, `02_stage/`, `03_marts/`, `04_charts/`, `05_evidence/`, `06_reports/`, or `07_qa/`:

```bash
python3 src/main.py
python3 src/build_marts.py
python3 -m unittest tests.test_output_contract -q
python3 -m unittest tests.test_mart_outputs -q
```

Do not run these checks in public CI.

## Report-Generation Checks

Report, DOCX, Excel, render, and accepted-package checks may require local generated artifacts, LibreOffice, chart images, and memo package folders. Run them only when the task explicitly authorizes report validation or regeneration.

## Accepted-Package Smoke Check

Verify accepted package artifacts without regenerating reports:

```bash
python3 scripts/verify_accepted_ollama_report_packages.py
```

The macOS launcher `run_all_reports_ollama_factory_check.command` wraps the same accepted-package verification path.

## Safety

Tests and smoke checks must not modify `02_stage/`, `03_marts/`, or final memo outputs unless a task explicitly authorizes that behavior.
