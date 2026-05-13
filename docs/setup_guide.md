# Setup Guide

## 1. Validate repository

```bash
bash scripts/validate_repo.sh
python3 scripts/static_workflow_audit.py
python3 scripts/pre_n8n_readiness_check.py
```

## 2. Prepare n8n credentials

Create the n8n credentials listed in `docs/credential_mapping.md`. Do not create env files for this repo.

## 3. Import active workflows only

```bash
bash scripts/n8n_import_preflight.sh
```

The script imports `workflows/active/` when the n8n CLI is installed. Archived v1 debug workflows are rollback references and are not imported by default.

## 4. Attach credentials in n8n

Attach credentials named in `docs/credential_mapping.md`:

- `POSTGRES_AI_CONTENT_DB`
- `GOOGLE_DRIVE_AI_CONTENT`
- `AI_LLM_HTTP_AUTH`
- `AI_AGENT_WEBHOOK_AUTH`

## 5. Run sandbox dry-run

Use `tests/sandbox_test_plan.md` and the payloads in `tests/payloads/`.

For day-to-day operation, follow `docs/operator_manual.md`.

## 6. Promote only after live sandbox checks

Do not mark the system production-ready until n8n has executed Postgres, Drive, LLM, supervisor, and notification paths successfully with test data.


## 7. PR #7 repaired validation focus

The validation scripts now fail if active workflows use env variables, if public webhooks lack n8n header-auth credentials, if service nodes lack declared n8n credentials, if approval gates do not branch before downstream work, if dry-run branches call live LLM/Drive nodes, if Code nodes contain likely unreachable top-level return patterns, or if active imports target anything outside `workflows/active/`.
