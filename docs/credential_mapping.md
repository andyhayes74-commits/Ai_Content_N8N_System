# Credential Mapping

This system uses n8n credentials only. Do not create env files and do not commit secrets or API keys to this repository.

## Required n8n credentials

| Credential name | n8n credential type | Used by |
|---|---|---|
| `AI_AGENT_WEBHOOK_AUTH` | HTTP Header Auth | `ai_content_orchestrator`, `api_supervisor_gateway`, `api_human_review_gateway` |
| `POSTGRES_AI_CONTENT_DB` | Postgres | all database read/write nodes |
| `GOOGLE_DRIVE_AI_CONTENT` | Google Drive OAuth2 | Drive folder, asset scan, and delivery pack nodes |
| `AI_LLM_HTTP_AUTH` | HTTP Header Auth | OpenAI-compatible LLM request nodes |

## Non-secret runtime fields

These values can be edited in n8n node settings or passed in payloads where supported:

| Value | Where used |
|---|---|
| LLM base URL | LLM HTTP Request node `url`; defaults to OpenAI-compatible chat completions URL |
| LLM model | LLM request body; defaults to `gpt-4o-mini` |
| Default parent Drive folder ID | `default_parent_drive_folder_id` payload field or Drive node parent field |

## Workflow credential needs

| Workflow | Public webhook auth | Postgres | LLM | Google Drive |
|---|---:|---:|---:|---:|
| `ai_content_orchestrator` | yes | via tools | via tools | via tools |
| `api_supervisor_gateway` | yes | yes | routed | routed |
| `api_human_review_gateway` | yes | yes | no | no |
| `tool_job_intake` | no | yes | no | no |
| `tool_drive_assets` | no | yes | no | yes |
| `tool_request_analysis` | no | yes | yes | no |
| `tool_content_planning` | no | yes | yes | no |
| `tool_content_generation` | no | yes | yes | no |
| `tool_qa_delivery` | no | yes | yes | yes |
| `tool_logging` | no | yes | no | no |
