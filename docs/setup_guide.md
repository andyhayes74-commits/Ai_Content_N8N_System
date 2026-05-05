# Setup Guide

## Required credentials/config
- Postgres n8n credential: `POSTGRES_AI_CONTENT_DB`.
- Google Drive n8n credential: `GOOGLE_DRIVE_AI_CONTENT`.
- OpenAI or LiteLLM credential/HTTP auth: `HTTP_OPENAI_OR_LITELLM` when live model calls are wired.
- Environment variables from `.env.example`, especially `AGENT_WEBHOOK_SECRET` and `DEFAULT_PARENT_DRIVE_FOLDER_ID`.

## Setup steps
1. Copy `.env.example` to `.env` and fill placeholders.
2. Provision Postgres and run `database/schema.sql`, then `database/seed_reference.sql`.
3. Import `workflows/*.json` into an n8n sandbox instance.
4. Attach the Postgres credential to all Postgres nodes.
5. Configure Google Drive credentials before live folder/file operations.
6. Configure OpenAI/LiteLLM before replacing dry-run generated payloads with live model calls.
7. Run `bash scripts/validate_repo.sh` locally if cloning the repo.
8. Follow `tests/sandbox_test_plan.md`.

## Safety reminder
No workflow should publish, send final client deliverables, delete Drive files, change credentials, or modify the database schema.
