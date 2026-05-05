# AI Content n8n System (v1.0 Release Candidate)

Credentials-ready n8n automation core for freelance AI content jobs. This repair branch focuses on the executable core path: real job creation, approval records, final human approval, core output persistence, QA status updates, and delivery gating.

## Safety
No delete, publish, or final client-send workflows. Final delivery approval requires `reviewer_type='human'`.

## Quick start
1. Fill `.env.example` values.
2. Apply `database/schema.sql` and `database/seed_reference.sql`.
3. Import `workflows/*.json` into a test n8n instance.
4. Configure `POSTGRES_AI_CONTENT_DB` and `GOOGLE_DRIVE_AI_CONTENT` credentials.
5. Follow `tests/sandbox_test_plan.md`.

## Not live-tested here
n8n import, live Postgres execution, Google Drive OAuth, OpenAI/LiteLLM calls, and OpenClaw/Hermes callbacks remain to be tested in your environment.
