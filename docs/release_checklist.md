# v1.0 RC Release Checklist

## Repository checks
- [x] Required workflow files exist.
- [x] Workflow files are valid JSON.
- [x] Required Postgres tables exist in `database/schema.sql`.
- [x] Validation scripts scan for malformed expressions and forbidden actions.
- [x] Secrets are represented by placeholders only.

## Functional sandbox checks still required in n8n
- [ ] Import all workflows into n8n sandbox.
- [ ] Configure Postgres credentials.
- [ ] Run `create_content_job` with `examples/client_brief.json`.
- [ ] Confirm rows appear in `content_jobs`, `content_tasks`, `content_events`.
- [ ] Run analysis/plan/final approval gates.
- [ ] Confirm outputs appear in `content_outputs`.
- [ ] Confirm final delivery is blocked until `api_approve_final_delivery` with `reviewer_type='human'`.
- [ ] Configure Google Drive and test folder/file operations.
- [ ] Configure OpenAI/LiteLLM and test live model calls.

## Not allowed
- [ ] No autonomous publishing.
- [ ] No final client sending.
- [ ] No file deletion.
- [ ] No credential/schema modification via supervisor API.
