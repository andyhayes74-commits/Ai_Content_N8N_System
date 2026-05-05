# Agent Supervisor API
Webhook prefix: `/v1/`.

Endpoints map to workflow files:
- `api_create_job`, `api_submit_message`, `api_attach_drive_folder`
- `api_check_job_status`, `api_list_active_jobs`
- `api_progress_updates`, `api_error_reports`
- `api_approve_analysis`, `api_approve_plan`, `api_request_revisions`
- `api_retry_step`, `api_pause_job`, `api_resume_job`, `api_cancel_job`

## Safety Boundaries
Agent layer must not delete files, publish content, send final deliverables, alter credentials/schema, or bypass human approval.
