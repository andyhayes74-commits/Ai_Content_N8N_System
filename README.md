# AI Content n8n System

**Version:** v1.0 Release Candidate  
**Status:** credentials-ready sandbox baseline  
**Repository purpose:** modular n8n automation system for freelance AI content generation work.

This repository contains a database-backed n8n workflow system for handling AI-assisted client content jobs. The system is designed to accept a client brief, register supporting assets, create a request analysis, generate a content plan, route content-output tasks, store generated outputs, run QA, prepare a delivery pack, and keep a supervisor agent informed.

It is designed for **sandbox import and testing first**, not immediate production use.

---

## Current status

This repo is now a **credentials-ready, database-backed v1.0 release candidate**.

Implemented in GitHub:

- modular n8n workflow JSON files
- Postgres schema and seed/reference data
- structured prompt files
- JSON schemas for AI outputs
- sandbox examples and fixtures
- validation and static audit scripts
- setup, failure-recovery, supervisor API, audit, and release-checklist docs
- database-backed workflow logic for the core job lifecycle

Not yet live-tested:

- n8n import/runtime execution
- Postgres runtime execution
- Google Drive OAuth folder/file actions
- OpenAI or LiteLLM model calls
- OpenClaw/Hermes supervisor callbacks
- notification webhook delivery

Do not treat this as production-ready until it has been imported into a test n8n instance and run end-to-end with test credentials.

---

## Architecture

The system uses:

| Layer | Role |
|---|---|
| n8n | workflow execution and webhook/API layer |
| Postgres | durable job state and source of truth |
| Google Drive | client project workspace and file storage |
| OpenAI or LiteLLM | AI analysis, planning, generation, and QA once wired in n8n |
| OpenClaw or Hermes | optional AI supervisor agent |
| Human approval | required before final delivery |

The system deliberately avoids one giant fragile workflow. Instead, it uses smaller workflows that write state to Postgres and can be tested independently.

---

## Repository layout

```text
workflows/   n8n workflow JSON files
prompts/     prompt templates for AI tasks
schemas/     JSON schemas for structured AI outputs
database/    Postgres schema and seed data
docs/        setup, audit, recovery, supervisor API, checklist
examples/    sandbox fixtures and example payloads
tests/       sandbox test plan
scripts/     static validation and workflow audit scripts
```

---

## Core workflow lifecycle

Expected sandbox path:

1. Create content job.
2. Register or prepare Google Drive project folder metadata.
3. Register/scan assets.
4. Parse or mark assets appropriately.
5. Create asset index.
6. Analyse client request.
7. Human/agent approves request analysis.
8. Generate content plan.
9. Human/agent approves content plan.
10. Route output tasks.
11. Generate/store requested content outputs.
12. QA-check outputs.
13. Notify user for review.
14. Human approves final delivery.
15. Generate delivery pack.
16. Job becomes `delivery_ready`.

Final delivery is **not sent automatically**.

---

## Implemented safety boundaries

The supervisor agent must not:

- delete files
- publish content
- send final client deliverables
- change credentials
- modify database schema
- edit n8n workflows directly
- approve final delivery without human approval

Final delivery approval requires:

```json
{
  "reviewer_type": "human"
}
```

The delivery workflow checks for an approved `final_delivery` approval before creating the delivery pack.

---

## Human approval gates

The system includes three approval gates:

| Gate | Approval stage | Required before |
|---|---|---|
| Request analysis approval | `analysis` | content plan generation |
| Content plan approval | `plan` | output generation |
| Final delivery approval | `final_delivery` | delivery pack creation |

Analysis and plan approvals may be handled by the supervisor layer if configured. Final delivery approval is human-only.

---

## Main Postgres tables

The schema includes:

```text
content_jobs
content_assets
content_outputs
content_tasks
content_events
content_errors
content_approvals
client_profiles
job_messages
```

Postgres is the source of truth. AI models should not be expected to remember job state.

---

## Job statuses

The job status model includes:

```text
created
intake_complete
assets_scanning
assets_parsed
analysis_complete
waiting_for_analysis_approval
waiting_for_plan_approval
generating_outputs
qa_in_progress
waiting_for_human_review
delivery_ready
completed
failed
paused
cancelled
```

---

## Google Drive project folder structure

Each client job should use this structure:

```text
ClientName_ProjectName_Date/
├── 00_Admin/
├── 01_Input/
├── 02_Parsed/
├── 03_Strategy/
├── 04_Copy/
├── 05_Images/
├── 06_Video/
└── 07_Delivery/
```

Current Drive workflows are credentials-ready and database-backed, but live Google Drive OAuth folder/file actions still need sandbox testing in n8n.

---

## Required credentials and config

Create or configure these before sandbox testing:

### Postgres

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=ai_content
POSTGRES_USER=ai_content_user
POSTGRES_PASSWORD=CHANGE_ME
```

Suggested n8n credential name:

```text
POSTGRES_AI_CONTENT_DB
```

### n8n

```env
N8N_BASE_URL=https://n8n.example.com
N8N_API_KEY=CHANGE_ME
```

The n8n API key is optional unless scripts or supervisor agents need to call n8n’s API directly.

### Google Drive

```env
GOOGLE_DRIVE_CREDENTIAL_ID=google-drive-credential-id
DEFAULT_PARENT_DRIVE_FOLDER_ID=drive-parent-folder-id
```

Suggested n8n credential name:

```text
GOOGLE_DRIVE_AI_CONTENT
```

### OpenAI or LiteLLM

```env
OPENAI_API_KEY=CHANGE_ME
LITELLM_BASE_URL=https://litellm.example.com
```

Use OpenAI direct or route through LiteLLM. Live model calls still need to be wired/tested in n8n.

Suggested n8n credential name:

```text
HTTP_OPENAI_OR_LITELLM
```

### Supervisor agent secret

```env
AGENT_WEBHOOK_SECRET=CHANGE_ME
```

Supervisor calls must send this header:

```text
x-agent-secret: <AGENT_WEBHOOK_SECRET>
```

### Notifications

```env
NOTIFICATION_WEBHOOK_URL=https://hooks.example.com/notify
```

Notification delivery is not live-tested yet.

---

## Quick start for sandbox testing

1. Clone the repo.
2. Copy `.env.example` to `.env` and fill placeholders.
3. Provision Postgres.
4. Run:

```bash
psql "$DATABASE_URL" -f database/schema.sql
psql "$DATABASE_URL" -f database/seed_reference.sql
```

Or apply the SQL manually using your Postgres tool.

5. Import `workflows/*.json` into a **test n8n instance**.
6. Attach the Postgres credential to all Postgres nodes.
7. Configure `AGENT_WEBHOOK_SECRET` for webhook authentication.
8. Run the sandbox path in `tests/sandbox_test_plan.md`.
9. Inspect:

```text
content_jobs
content_tasks
content_outputs
content_events
content_errors
content_approvals
content_assets
job_messages
```

Do not use this with real client work until sandbox testing passes.

---

## Validation scripts

Run these from the repo root:

```bash
bash scripts/validate_repo.sh
python scripts/static_workflow_audit.py
```

The validation script checks:

- required workflow files exist
- workflow JSON parses
- schema/example JSON parses
- required table names exist
- required workflow/table operations are present
- malformed n8n expression patterns are absent
- obvious forbidden actions are absent
- obvious hardcoded secret patterns are absent
- required `.env.example` placeholders exist

This does **not** replace live n8n testing.

---

## Content outputs supported

The system supports storing:

- request analysis
- asset index
- content plan
- campaign plan
- social media posts
- email copy
- blog/article copy
- image prompts
- video scripts
- QA report
- delivery pack

Generation workflows currently support dry-run/generated payload storage. Live OpenAI/LiteLLM generation should be wired and tested inside n8n after credentials are configured.

---

## AI quality and safety rules

Generated content must not invent unsupported client facts, including:

- dates
- prices
- claims
- statistics
- product features
- locations
- guarantees
- testimonials
- endorsements

Missing information should be flagged clearly. Risky, legally sensitive, medical, financial, or claim-heavy content should be marked for human review.

The system should separate:

```text
facts
assumptions
missing information
risk flags
source material used
```

---

## Supervisor API layer

Supervisor workflows support:

- create job
- submit message
- attach Drive folder
- check job status
- list active jobs
- get progress updates
- get error reports
- approve analysis
- approve plan
- request revisions
- retry safe failed steps
- pause job
- resume job
- cancel job

The supervisor may not approve final delivery unless the request satisfies the human-only final delivery approval requirements.

See:

```text
docs/supervisor_api.md
```

---

## Important limitations

This release candidate is ready for sandbox testing, but these remain unproven until tested in your environment:

- n8n workflow import compatibility
- n8n node credential assignment
- Postgres query execution from n8n
- Google Drive OAuth actions
- OpenAI/LiteLLM HTTP calls
- OpenClaw/Hermes webhook calls
- notification webhook delivery

Treat any failure found during sandbox testing as expected integration hardening, not a production incident.

---

## Recommended next stage

The next stage is:

```text
n8n sandbox import + Postgres-first test
```

Recommended order:

1. Test Postgres-only workflows first.
2. Test approval gates.
3. Test dry-run generated outputs.
4. Test QA and delivery gating.
5. Add Google Drive credentials.
6. Add OpenAI/LiteLLM credentials.
7. Add supervisor agent callbacks.
8. Only then consider production hardening.

---

## Release label recommendation

Use this as:

```text
v1.0 RC sandbox baseline
```

Do **not** label it as a finished production system yet.
