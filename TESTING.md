# Testing

## Run All Unit Tests

```bash
python3 -m unittest discover -s tests -q
```

This is the default non-Ollama unit test command.

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

## Accepted-Package Smoke Check

Verify accepted package artifacts without regenerating reports:

```bash
python3 scripts/verify_accepted_ollama_report_packages.py
```

The macOS launcher `run_all_reports_ollama_factory_check.command` wraps the same accepted-package verification path.

## Safety

Tests and smoke checks must not modify `02_stage/`, `03_marts/`, or final memo outputs unless a task explicitly authorizes that behavior.
