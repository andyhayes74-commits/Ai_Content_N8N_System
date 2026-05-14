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

## 5. Apply database schema and migrations

Apply `database/schema.sql` for new installs. For existing installs, apply migrations in order from `database/migrations/`.

Temporary webhook migration workflows are available in `workflows/placeholders/` when using n8n to apply a migration. Deactivate temporary migration workflows immediately after they return `migration_applied: true`.

## 6. Run sandbox dry-run

Use `tests/sandbox_test_plan.md` and the payloads in `tests/payloads/`.

For day-to-day operation, follow `docs/operator_manual.md`.

## 7. Run v3 smoke test

After deployment, run:

```bash
N8N_BASE_URL="https://n8n.example.com" \
N8N_API_KEY="..." \
AI_AGENT_WEBHOOK_AUTH="..." \
node scripts/production_smoke_test.mjs
```

Or use the manual GitHub Action:

```text
Production smoke test
```

## 8. Promote only after live sandbox checks

Do not mark the system production-ready until n8n has executed Postgres, Drive, LLM, supervisor, and notification paths successfully with test data.


## Validation focus

The validation scripts now fail if active workflows use env variables, if public webhooks lack n8n header-auth credentials, if service nodes lack declared n8n credentials, if approval gates do not branch before downstream work, if dry-run branches call live LLM/Drive nodes, if Code nodes contain likely unreachable top-level return patterns, or if active imports target anything outside `workflows/active/`.
