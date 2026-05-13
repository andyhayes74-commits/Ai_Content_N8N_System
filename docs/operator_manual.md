# AI Content n8n System Operator Manual

## Purpose

The AI Content n8n System runs database-backed AI content jobs through n8n. It accepts a client/job brief, prepares Drive assets, analyzes the request, waits for human approvals, generates content, runs QA, and prepares a final delivery pack.

GitHub is the source of truth for workflow JSON. n8n is the runtime.

## Required n8n credentials

Create these credentials inside n8n before running live jobs:

| Credential | Type | Used for |
|---|---|---|
| `AI_AGENT_WEBHOOK_AUTH` | HTTP Header Auth | Public webhook access |
| `POSTGRES_AI_CONTENT_DB` | Postgres | Jobs, outputs, events, errors, approvals |
| `GOOGLE_DRIVE_AI_CONTENT` | Google Drive OAuth2 | Drive folders, assets, delivery pack |
| `AI_LLM_HTTP_AUTH` | HTTP Header Auth | OpenAI-compatible LLM calls |

Do not use env files. Do not store secrets in this repository.

## Import or deploy workflows

Use only the active workflows:

```text
workflows/active/
```

There are 10 active workflows:

1. `ai_content_orchestrator`
2. `tool_job_intake`
3. `tool_drive_assets`
4. `tool_request_analysis`
5. `tool_content_planning`
6. `tool_content_generation`
7. `tool_qa_delivery`
8. `tool_logging`
9. `api_supervisor_gateway`
10. `api_human_review_gateway`

For first setup, import `workflows/placeholders/` if you only need to create n8n workflow IDs for GitHub deployment. Then copy those IDs into GitHub secrets and run the deploy action to replace the placeholders with the real workflows from `workflows/active/`.

You can also import `workflows/active/` directly if you are ready to attach credentials immediately.

For ongoing updates, use the GitHub Action:

```text
Deploy AI Content workflows to n8n
```

Run it first with `dry_run=true`, then with `dry_run=false` after confirming the target workflow IDs are correct.

## Database setup

Apply:

```text
database/schema.sql
```

The main tables are:

- `content_jobs`
- `content_assets`
- `content_outputs`
- `content_tasks`
- `content_events`
- `content_errors`
- `content_approvals`
- `client_profiles`
- `job_messages`

Postgres is the source of truth for job state.

## Normal job lifecycle

```text
Create job
→ Prepare Drive workspace/assets
→ Analyze request
→ Human approves analysis
→ Generate content plan
→ Human approves plan
→ Generate outputs
→ QA review
→ Human approves final delivery
→ Create delivery pack
→ Mark delivery_ready
```

The system intentionally stops at approval gates. Content planning, content generation, and delivery pack creation should not continue until the matching approval exists.

## Main webhook entry points

Use the header configured in `AI_AGENT_WEBHOOK_AUTH` when calling public webhooks.

| Workflow | Path | Purpose |
|---|---|---|
| `ai_content_orchestrator` | `v1/orchestrator` | Main lifecycle/action router |
| `api_supervisor_gateway` | `v1/supervisor` | Agent/supervisor API for status and allowed actions |
| `api_human_review_gateway` | `v1/human-review` | Human approval/revision decisions |

## Common actions

### Create a job

Send a payload like `tests/payloads/01_orchestrator_dry_run_job.json` to:

```text
v1/orchestrator
```

Use:

```json
{
  "action": "create_job",
  "mode": "dry_run",
  "external_job_ref": "sandbox-operator-001",
  "project_name": "Example Content Job",
  "brief_text": "Create a campaign package for a product launch.",
  "requested_outputs": ["campaign_plan", "social_posts", "email_copy"],
  "drive_folder_id": "optional-existing-drive-folder"
}
```

### Check job status

Send to:

```text
v1/supervisor
```

```json
{
  "action": "check_status",
  "job_id": "00000000-0000-0000-0000-000000000000"
}
```

### Approve analysis

Send to:

```text
v1/human-review
```

```json
{
  "job_id": "00000000-0000-0000-0000-000000000000",
  "approval_stage": "analysis",
  "decision": "approved",
  "reviewer_name": "operator",
  "notes": "Analysis approved."
}
```

### Approve plan

```json
{
  "job_id": "00000000-0000-0000-0000-000000000000",
  "approval_stage": "plan",
  "decision": "approved",
  "reviewer_name": "operator",
  "notes": "Plan approved."
}
```

### Approve final delivery

```json
{
  "job_id": "00000000-0000-0000-0000-000000000000",
  "approval_stage": "final_delivery",
  "decision": "approved",
  "reviewer_name": "operator",
  "notes": "Final delivery approved."
}
```

Supported decisions:

- `approved`
- `revision_requested`
- `rejected`

## Dry-run vs live mode

Use `mode: "dry_run"` for safe testing. Dry-run bypasses live LLM and Drive calls where possible and uses fallback payloads.

Use `mode: "live"` only after:

- n8n credentials are attached
- Postgres schema is applied
- webhooks authenticate correctly
- a dry-run lifecycle has passed
- an operator is ready to review approval gates

## Generated outputs

The content generation workflow can dispatch:

- `campaign_plan`
- `social_posts`
- `email_copy`
- `blog_article`
- `image_prompts`
- `video_scripts`

Outputs are stored in `content_outputs`. Generation tasks are tracked in `content_tasks`.

## Delivery pack

The delivery pack is created only after final human approval. It collects stored outputs, records included output metadata, stores Drive upload metadata when available, and marks the job:

```text
delivery_ready
```

## Operator checks

Before a live run:

```bash
bash scripts/validate_repo.sh
python3 scripts/static_workflow_audit.py
python3 scripts/pre_n8n_readiness_check.py
```

For n8n import shape:

```bash
bash scripts/n8n_import_preflight.sh
```

For GitHub-to-n8n deployment, run the GitHub Action with:

```text
dry_run=true
```

Then run again with:

```text
dry_run=false
```

## Troubleshooting

If a workflow stops at an approval gate, check `content_approvals` for the required row:

- `approval_stage='analysis'`
- `approval_stage='plan'`
- `approval_stage='final_delivery'`

If a job does not appear to progress, check:

- `content_jobs.status`
- `content_events`
- `content_errors`
- n8n execution logs
- credential attachment on Postgres, Drive, LLM, and webhook nodes

If deployment fails, keep the existing n8n workflows unchanged and inspect the GitHub Action log. The deploy script redacts the n8n API key from errors.

## Safety rules

- Do not import archived workflows during normal operation.
- Do not edit live n8n workflows without exporting reviewed changes back to GitHub.
- Do not bypass approval gates.
- Do not store API keys or secrets in repo files.
- Do not activate live mode until dry-run and credential tests pass.
