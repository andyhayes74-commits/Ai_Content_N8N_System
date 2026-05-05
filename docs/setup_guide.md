# Setup Guide

This guide is for the pre-n8n transfer baseline.

## Before import

Run these from the repo root:

```bash
bash scripts/validate_repo.sh
python scripts/static_workflow_audit.py
python scripts/pre_n8n_readiness_check.py
bash scripts/n8n_import_preflight.sh
```

The validation/preflight scripts regenerate live-mode LLM and Drive workflow JSONs before checking/importing:

```bash
python scripts/build_llm_workflows.py
python scripts/build_drive_workflows.py
```

Do not import stale workflow files without running the preflight scripts.

## Required credentials/config

- Postgres n8n credential: `POSTGRES_AI_CONTENT_DB`.
- Google Drive n8n credential or OAuth marker: `GOOGLE_DRIVE_AI_CONTENT`.
- OpenAI/LiteLLM HTTP credential: `HTTP_OPENAI_OR_LITELLM`.
- Environment variables from `.env.example`, especially `AGENT_WEBHOOK_SECRET`, `OPENAI_MODEL`, `LITELLM_BASE_URL`, `LITELLM_API_KEY`, and `DEFAULT_PARENT_DRIVE_FOLDER_ID`.

## Setup steps

1. Copy `.env.example` to `.env` and fill placeholders.
2. Provision Postgres.
3. Run `database/schema.sql`, then `database/seed_reference.sql`.
4. Run the preflight scripts above.
5. Import workflows into an n8n sandbox instance using CLI/import folder flow.
6. Attach the Postgres credential to Postgres nodes.
7. Configure LLM credentials/env values.
8. Configure Google Drive credentials/env values.
9. Run `tests/sandbox_test_plan.md` using dry-run payloads first.
10. After dry-run success, test live LLM calls and Drive actions with test-only data.

## Safety reminder

This system is designed around human review gates. Final client handoff remains outside autonomous workflow execution.
