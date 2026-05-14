# Current Baseline

Date: 2026-05-14

## Canonical reference

`docs/system_source_of_truth.md` is the controlling development brief. The current system is a working transitional v1 pipeline, not the finished modular platform.

## Branches

- `main`: source-of-truth brief and merged v1 baseline history.
- `codex/finish-ai-content-n8n-system`: active implementation branch for the activated n8n system and v2 planning work.

## Current runtime state

The active workflow set has been deployed to `https://n8n.hayfam.co.uk` and activated in n8n.

The current active workflows are:

- `ai_content_orchestrator`
- `api_supervisor_gateway`
- `api_human_review_gateway`
- `tool_job_intake`
- `tool_drive_assets`
- `tool_request_analysis`
- `tool_content_planning`
- `tool_content_generation`
- `tool_qa_delivery`
- `tool_logging`

The baseline dry-run test created/updated job:

```text
170be04b-5584-4274-bcdd-623c2d62a402
```

The job reached:

```text
waiting_for_analysis_approval
```

Supervisor `check_status` returned:

```text
output_count: 3
open_error_count: 0
```

## Runtime-only n8n state

These items are intentionally not stored in GitHub:

- credential secret values,
- Google OAuth token data,
- Postgres password and connection secret values,
- active/inactive runtime state unless explicitly controlled by deployment,
- execution history,
- live test jobs and generated data.

Required n8n credentials:

- `AI_AGENT_WEBHOOK_AUTH`
- `AI_LLM_HTTP_AUTH`
- `POSTGRES_AI_CONTENT_DB`
- `GOOGLE_DRIVE_AI_CONTENT`

Important: `AI_AGENT_WEBHOOK_AUTH` was temporarily set to a test bearer token during smoke testing. Replace it with the permanent operator token before real use.

## GitHub source-of-truth state

The repository contains the workflow structure and deploy behaviour needed to reproduce the activated workflow definitions:

- credential IDs are resolved during deployment by credential name,
- Execute Workflow references are resolved during deployment by workflow ID map,
- Google Drive nodes use the credential slot expected by the current n8n version,
- parse-warning database nodes pass a row forward when no warning is inserted,
- the temporary Postgres setup workflow is stored in `workflows/placeholders/TEMP_setup_ai_content_postgres_schema.json`.

## Next target

The next development target is:

```text
v2.1 - Tool Registry and Planner Awareness
```

Do not build large numbers of specialist tools before the runtime registry and planner awareness are in place.
