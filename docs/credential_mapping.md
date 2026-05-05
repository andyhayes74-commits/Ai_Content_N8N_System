# Credential Mapping

This document lists the credentials/config values required after importing the workflows into n8n.

## Global config

| Purpose | Placeholder/config |
|---|---|
| Postgres host | `POSTGRES_HOST` |
| Postgres port | `POSTGRES_PORT` |
| Postgres DB | `POSTGRES_DB` |
| Postgres user | `POSTGRES_USER` |
| Postgres password | `POSTGRES_PASSWORD` |
| n8n base URL | `N8N_BASE_URL` |
| n8n API key | `N8N_API_KEY` |
| Agent webhook auth | `AGENT_WEBHOOK_SECRET` |
| Notification target | `NOTIFICATION_WEBHOOK_URL` |

## n8n credentials

| Area | Suggested n8n credential name |
|---|---|
| Postgres | `POSTGRES_AI_CONTENT_DB` |
| Google Drive | `GOOGLE_DRIVE_AI_CONTENT` |
| OpenAI/LiteLLM HTTP | `HTTP_OPENAI_OR_LITELLM` |

## LLM config

| Purpose | Placeholder/config |
|---|---|
| OpenAI key | `OPENAI_API_KEY` |
| OpenAI model | `OPENAI_MODEL` |
| LiteLLM base URL | `LITELLM_BASE_URL` |
| LiteLLM API key | `LITELLM_API_KEY` |

Use either OpenAI directly or LiteLLM. If using LiteLLM, set `LITELLM_BASE_URL` to the OpenAI-compatible `/v1` base URL.

## Google Drive config

| Purpose | Placeholder/config |
|---|---|
| n8n Google Drive credential marker | `GOOGLE_DRIVE_CREDENTIAL_ID` |
| Parent folder for client jobs | `DEFAULT_PARENT_DRIVE_FOLDER_ID` |

## Workflow groups

| Workflow group | Postgres | LLM | Google Drive | Agent secret |
|---|---:|---:|---:|---:|
| Job creation | yes | no | no | yes |
| Asset registration/index | yes | optional | yes for live Drive | yes |
| Request analysis | yes | yes | no | yes |
| Content plan | yes | yes | no | yes |
| Output generation | yes | yes | no | yes |
| QA | yes | yes | no | yes |
| Delivery pack | yes | optional | yes for saving files | yes |
| Supervisor APIs | yes | no | optional | yes |
