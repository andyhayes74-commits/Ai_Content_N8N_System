# v1.0 RC Audit (ChatGPT Repair Branch)

Audit date: 2026-05-05.

## Status
This branch is now a credentials-ready, database-backed release candidate for sandbox import testing. It is not production-tested yet.

## Implemented
- Real job creation through `create_content_job` and `api_create_job`.
- Agent secret validation on webhook workflows using `x-agent-secret`.
- Real approval rows for analysis, plan, and final delivery.
- Final delivery approval requires `reviewer_type='human'`.
- Request analysis, asset index, content plan, generation outputs, QA report, and delivery pack are persisted in `content_outputs`.
- Assets are registered and indexed through `content_assets`.
- Audio/video references are marked honestly as reference-only unless transcription is wired later.
- Supervisor status, progress, error, pause, resume, cancel, revision, message, and retry workflows are database-backed.
- Validation scripts check workflow presence, JSON syntax, table-action markers, bad n8n expression patterns, forbidden destructive/publish/send terms, and obvious hardcoded secret patterns.

## Credential-ready but not live-tested
- Live n8n workflow import.
- Live Postgres execution.
- Google Drive OAuth folder/file creation and listing.
- OpenAI/LiteLLM model calls.
- OpenClaw/Hermes live supervisor callbacks.
- Notification webhook delivery.

## Known limitations
- Model calls are represented by dry-run/generated payload entry points. Live OpenAI/LiteLLM HTTP nodes should be wired and tested in n8n once credentials exist.
- Google Drive workflows record metadata and are prepared for credentials, but do not yet prove live Drive folder/file operations.
- The repo is ready for sandbox testing, not client production use.

## First sandbox path
1. Import workflows into a test n8n instance.
2. Configure Postgres credential and apply `database/schema.sql`.
3. Create a job via `create_content_job`.
4. Register or prepare Drive folder metadata.
5. Register assets and create asset index.
6. Store request analysis, approve analysis, store content plan, approve plan.
7. Route tasks and generate outputs using dry-run payloads.
8. Run QA, human final approval, and delivery pack.
9. Inspect `content_jobs`, `content_outputs`, `content_events`, `content_errors`, and `content_approvals`.
