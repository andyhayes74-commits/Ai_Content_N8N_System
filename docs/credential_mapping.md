# Credential Mapping

## Environment/config placeholders

| Purpose | Placeholder/config |
|---|---|
| Postgres host | `POSTGRES_HOST` |
| Postgres port | `POSTGRES_PORT` |
| Postgres DB | `POSTGRES_DB` |
| Postgres user | `POSTGRES_USER` |
| Postgres password | `POSTGRES_PASSWORD` |
| n8n base URL for future API deployment | `N8N_BASE_URL` |
| n8n API key for future API deployment | `N8N_API_KEY` |
| Google Drive credential marker | `GOOGLE_DRIVE_CREDENTIAL_ID` |
| Default parent Drive folder | `DEFAULT_PARENT_DRIVE_FOLDER_ID` |
| Google Drive access token for HTTP fallback | `GOOGLE_DRIVE_ACCESS_TOKEN` |
| OpenAI key | `OPENAI_API_KEY` |
| OpenAI/LiteLLM model | `OPENAI_MODEL` |
| LiteLLM OpenAI-compatible base URL | `LITELLM_BASE_URL` |
| LiteLLM key | `LITELLM_API_KEY` |
| Agent/supervisor webhook secret | `AGENT_WEBHOOK_SECRET` |
| Human/operator notification target | `NOTIFICATION_WEBHOOK_URL` |

## Suggested n8n credentials

| Area | Suggested n8n credential name | Used by |
|---|---|---|
| Postgres | `POSTGRES_AI_CONTENT_DB` | all tool workflows and gateways |
| Google Drive | `GOOGLE_DRIVE_AI_CONTENT` | `tool_drive_assets`, `tool_qa_delivery` |
| OpenAI/LiteLLM HTTP | `HTTP_OPENAI_OR_LITELLM` | analysis, planning, generation, QA |

## Workflow credential needs

| Workflow | Postgres | LLM | Google Drive | Agent secret |
|---|---:|---:|---:|---:|
| `ai_content_orchestrator` | via tools | via tools | via tools | yes |
| `tool_job_intake` | yes | no | no | yes |
| `tool_drive_assets` | yes | optional | yes | yes |
| `tool_request_analysis` | yes | yes | no | yes |
| `tool_content_planning` | yes | yes | no | yes |
| `tool_content_generation` | yes | yes | no | yes |
| `tool_qa_delivery` | yes | yes | yes | yes |
| `tool_logging` | yes | no | no | yes |
| `api_supervisor_gateway` | yes | routed | routed | yes |
| `api_human_review_gateway` | yes | no | no | yes |
