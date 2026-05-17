# AI Content n8n System Operator Manual

## Purpose

The AI Content n8n System runs database-backed AI content jobs through n8n. It accepts a client/job brief, prepares Drive assets, creates a registry-aware execution plan, runs selected tools, performs QA and safe repair auditing, handles policy-driven approvals, and prepares a final delivery pack.

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
→ Human approves analysis where policy requires it
→ Generate content plan
→ Human approves plan where policy requires it
→ Generate outputs
→ QA review and safe repair audit
→ Human approves final delivery where policy requires it
→ Create delivery pack
→ Mark delivery_ready
```

The system stops at approval gates according to job/client policy. Low-risk dry-runs can use `qa_only`; full staged review can use `full_staged`.

## Approval policies

Supported policies:

- `none` - no staged approval in dry-run paths.
- `qa_only` - run plan and delivery after QA if there are no blocking issues.
- `operator_final` - lighter early gates, final operator approval still expected.
- `full_staged` - analysis, plan, and final approval gates.
- `client_review_required` - preserves client/human review expectations.

Agents cannot impersonate human approval. Human-only final approvals must come through `api_human_review_gateway`.

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
  "drive_folder_id": "optional-existing-drive-folder",
  "approval_policy": "qa_only"
}
```

You can also send a client profile. If `requested_outputs` is omitted, `client_profile.output_defaults.requested_outputs` can provide the defaults.

```json
{
  "action": "create_job",
  "mode": "dry_run",
  "external_job_ref": "sandbox-client-001",
  "project_name": "Client Default Job",
  "brief_text": "Create content using client defaults.",
  "drive_folder_id": "optional-existing-drive-folder",
  "client_profile": {
    "client_code": "demo_client",
    "client_name": "Demo Client",
    "default_approval_policy": "qa_only",
    "forbidden_claims": ["guaranteed results"],
    "output_defaults": {
      "requested_outputs": ["social_posts", "email_copy"]
    }
  }
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

## QA repair audit

QA reports can include structured `issues`. Repairable issues create records in `content_repair_attempts`; blocking issues keep the job in human review. Repair is audited, not hidden.

Use `tests/payloads/07_qa_repair_dry_run.json` as the repair-case payload reference.

## Asset modules

Drive asset indexing can create reusable client asset modules in `content_asset_modules`. The planner receives active asset modules for the client and includes them in `tool_execution_plan.asset_modules`.

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

For the v3 smoke test, run:

```bash
N8N_BASE_URL="https://n8n.example.com" \
N8N_API_KEY="..." \
AI_AGENT_WEBHOOK_AUTH="..." \
node scripts/production_smoke_test.mjs
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
