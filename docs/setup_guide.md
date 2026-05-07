# Setup Guide

## 1. Validate repository

```bash
bash scripts/validate_repo.sh
python scripts/static_workflow_audit.py
python scripts/pre_n8n_readiness_check.py
```

## 2. Configure environment

Copy `.env.example` to the deployment environment and set Postgres, Google Drive, OpenAI/LiteLLM, supervisor secret, and notification values. Do not commit real secrets.

## 3. Import active workflows only

```bash
bash scripts/n8n_import_preflight.sh
```

The script imports `workflows/active/` when the n8n CLI is installed. Archived v1 debug workflows are rollback references and are not imported by default.

## 4. Attach credentials in n8n

Attach credentials named in `docs/credential_mapping.md`:

- `POSTGRES_AI_CONTENT_DB`
- `GOOGLE_DRIVE_AI_CONTENT`
- `HTTP_OPENAI_OR_LITELLM`

## 5. Run sandbox dry-run

Use `tests/sandbox_test_plan.md` and the payloads in `tests/payloads/`.

## 6. Promote only after live sandbox checks

Do not mark the system production-ready until n8n has executed Postgres, Drive, LLM, supervisor, and notification paths successfully with test data.
