# v3 Production Runbook

## Source Of Truth

GitHub is the source of truth for workflow JSON, schemas, migrations, registry files, and operator docs. n8n is the runtime. Credentials stay in n8n credentials only.

## Required Checks

Run these before promoting a release:

```bash
bash scripts/validate_repo.sh
python3 scripts/static_workflow_audit.py
python3 scripts/pre_n8n_readiness_check.py
```

Run the production smoke test with secrets supplied by the shell or GitHub Actions:

```bash
N8N_BASE_URL="https://n8n.example.com" \
N8N_API_KEY="..." \
AI_AGENT_WEBHOOK_AUTH="..." \
node scripts/production_smoke_test.mjs
```

Do not commit secrets or `.env` files.

## Migration Check

Apply migrations through temporary n8n workflows or a controlled Postgres admin session. After each migration:

- confirm the migration returns `migration_applied: true`
- deactivate the temporary workflow
- deploy from GitHub again
- run the smoke test

## Credential Health

Confirm these n8n credentials exist before live operation:

- `POSTGRES_AI_CONTENT_DB`
- `GOOGLE_DRIVE_AI_CONTENT`
- `AI_LLM_HTTP_AUTH`
- `AI_AGENT_WEBHOOK_AUTH`

Dry-run mode should not require a Drive upload. Live mode does.

## Rollback

1. Re-run the deploy action from the last known good commit.
2. Keep workflows inactive only if an unsafe live behavior is found.
3. Do not edit live workflows directly except for emergency containment.
4. If an emergency edit is made in n8n, export it back to GitHub immediately.

## Backup And Export

Before live client use, schedule backups for:

- Postgres database
- n8n workflow exports
- n8n credential backup according to the deployment host policy
- Google Drive delivery folders

## Release Gate

A release is v3-ready when:

- fresh deploy succeeds
- smoke test reaches `delivery_ready`
- supervisor status works
- no recent workflow executions are failed for the smoke job
- delivery pack is recorded in Postgres
- errors and repair attempts are inspectable
