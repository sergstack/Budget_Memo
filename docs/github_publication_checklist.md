# GitHub Publication Checklist

Use this checklist before creating a public or shared GitHub repository.

- Confirm the repository is initialized intentionally and no commit/push has been made by automation.
- Run `git status --short` and review every tracked or staged file.
- Run `git ls-files` and confirm no raw data, stage data, marts, reports, QA artifacts, logs, caches, archives, secrets, or local outputs are tracked.
- Confirm `.env`, `.env.*`, credentials, tokens, cookies, keys, certificates, and service account files are ignored.
- Confirm `.env.example` contains placeholders only.
- Confirm corporate input/output folders remain local and ignored.
- If any confidential file was ever committed, stop before pushing, rotate affected secrets, and clean history only after explicit approval.
