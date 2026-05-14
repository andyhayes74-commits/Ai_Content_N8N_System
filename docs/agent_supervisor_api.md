# Agent Supervisor API

Webhook prefix: `/v1/`.

The active supervisor API is handled by:

- `api_supervisor_gateway` at `/v1/supervisor`
- `ai_content_orchestrator` at `/v1/orchestrator`
- `api_human_review_gateway` at `/v1/human-review`

All public webhook calls must include the n8n `AI_AGENT_WEBHOOK_AUTH` header credential.

## Common Supervisor Actions

Send these to `/v1/supervisor` unless noted otherwise:

- `check_status`
- `list_active_jobs`
- `progress_updates`
- `error_reports`
- `retry`
- `pause`
- `resume`
- `cancel`

Send lifecycle work to `/v1/orchestrator`:

- `create_job`
- `generate_plan`
- `run_plan`
- `continue_plan`
- `generate_outputs`
- `qa_delivery`

Send human decisions to `/v1/human-review`:

- `approval_stage: analysis`
- `approval_stage: plan`
- `approval_stage: final_delivery`
- `decision: approved | revision_requested | rejected`

## Safety Boundaries

The agent layer must not delete files, publish content, send final deliverables outside the delivery-pack workflow, alter credentials/schema, or bypass approval policy. Human-only approvals must go through `api_human_review_gateway`.
