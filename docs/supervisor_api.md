# Supervisor API
All `/v1/*` webhooks require `x-agent-secret: $AGENT_WEBHOOK_SECRET`.
Agent endpoints: create, submit_message, attach_drive_folder, check/list status, progress/errors, request_revisions, retry, pause/resume/cancel, approve analysis/plan.
Final delivery approval is human-only (`reviewer_id=andy`) and not part of agent approval endpoints.
