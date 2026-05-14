# Current Baseline

Date: 2026-05-14

## Canonical reference

`docs/system_source_of_truth.md` is the controlling development brief. The current system has moved beyond the transitional v1 pipeline into the v3 production-ready platform foundation.

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

Latest verified v3 smoke test:

```text
job_id: 84af3f7f-dfb8-4014-a441-e9e51f9a6e89
plan_id: cab03eae-a951-419a-8e06-4fd55d00e348
final_status: delivery_ready
```

The smoke test covered create job, generate plan, run plan, supervisor status, and recent n8n execution status checks.

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
- temporary migration workflows are stored under `workflows/placeholders/` for controlled setup/migration use only and should be deactivated after use.

## Implemented platform foundation

- Tool registry and planner awareness.
- Plan-driven orchestration.
- Policy-driven approvals.
- QA repair attempt auditing.
- Client profile rules/defaults.
- Reusable asset modules.
- Experimental specialist tool contracts.
- Production smoke test and v3 runbook.

The next product work is to promote specialist tools one by one from `registry/tools.experimental.json` into active workflows after each has a workflow ID, dry-run test, credential check, and limited live test.
