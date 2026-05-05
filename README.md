# AI Content n8n System v1.0 RC (Credentials-Ready)

Modular n8n + Postgres + Google Drive + OpenAI/LiteLLM content operations system.

## Required n8n Credentials
- `POSTGRES_AI_CONTENT_DB`
- `GOOGLE_DRIVE_AI_CONTENT`
- `HTTP_OPENAI_OR_LITELLM`

## Required Env Vars
See `.env.example`:
`POSTGRES_*`, `N8N_BASE_URL`, `GOOGLE_DRIVE_CREDENTIAL_ID`, `DEFAULT_PARENT_DRIVE_FOLDER_ID`, `OPENAI_API_KEY` or `LITELLM_*`, `AGENT_WEBHOOK_SECRET`, `NOTIFICATION_WEBHOOK_URL`.

## Workflow Behavior
- Webhooks validate `x-agent-secret`.
- Durable writes to `content_jobs`, `content_tasks`, `content_events`, `content_errors`, `content_approvals`, `content_outputs`.
- Approval gates enforced for analysis/plan/final delivery.
- No publish, no client-send, no destructive SQL.

## Run
1. Apply `database/schema.sql`.
2. Import workflows.
3. Run `scripts/validate_repo.sh`.
4. Follow `docs/sandbox_test_plan.md`.
