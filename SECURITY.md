# Security Policy

This public repository must not contain corporate source data, generated financial artifacts, secrets, or private configuration.

## What Must Stay Out Of Git

- `.env` files except `.env.example`.
- API keys, tokens, cookies, service account files, private keys, certificates, and credentials.
- Corporate Excel, CSV, Parquet, JSONL, database, DOCX, PDF, image, archive, log, and report artifacts.
- Ignored local data and output layers such as `01_raw/`, `02_stage/`, `03_marts/`, `06_reports/`, and `07_qa/`.

## Safety Controls

- `.gitignore` excludes known data, artifact, cache, and credential patterns.
- `scripts/check_repo_public_safety.py` checks Git-tracked files for forbidden folders and file extensions.
- GitHub CI runs data-free smoke checks only.

Run before publishing repository changes:

```bash
python3 scripts/check_repo_public_safety.py
```

## Reporting Accidental Exposure

If a secret, credential, corporate data file, or generated artifact is accidentally committed:

1. Stop pushing further changes.
2. Treat the exposed value as compromised.
3. Rotate affected secrets through the appropriate internal process.
4. Request explicit approval before any Git history cleanup.
5. Do not paste secret values into issues, PRs, logs, or chat.

History rewriting, BFG, or `git filter-repo` cleanup must be handled as a separate approved task.
