# AI Content n8n System

**Version:** v2 operator-ready workflow architecture  
**Status:** Ready for n8n sandbox import after operator review; not production-approved until live n8n execution and credentials are tested.

This repository is the GitHub source of truth for a database-backed n8n system that runs AI-assisted content jobs. The v2 build replaces the previous 40-workflow debug architecture with one main orchestrator and a small set of reusable callable tool workflows.

## Operator architecture

Active workflows live only in `workflows/active/`:

1. `ai_content_orchestrator.json` — controls the full job lifecycle.
2. `tool_job_intake.json` — creates/updates jobs and records inbound messages.
3. `tool_drive_assets.json` — prepares the Google Drive workspace and asset index.
4. `tool_request_analysis.json` — analyses the request and opens the analysis approval gate.
5. `tool_content_planning.json` — creates the plan after analysis approval and opens the plan gate.
6. `tool_content_generation.json` — dispatches approved output generation routes.
7. `tool_qa_delivery.json` — QA checks outputs, opens final human review, and creates delivery-pack metadata only after human approval.
8. `tool_logging.json` — progress/error logging and retry-safe markers.
9. `api_supervisor_gateway.json` — agent/supervisor API gateway for OpenClaw/Hermes/Julian-style callers.
10. `api_human_review_gateway.json` — human approval and revision gateway.

The old debug build is archived in `workflows/archive/v1_debug_build/` and should not be imported during normal operator setup.

## Lifecycle

```text
api_supervisor_gateway or operator call
→ ai_content_orchestrator
→ tool_job_intake
→ tool_drive_assets
→ tool_request_analysis
→ human analysis approval via api_human_review_gateway
→ tool_content_planning
→ human plan approval via api_human_review_gateway
→ tool_content_generation
→ tool_qa_delivery
→ human final approval via api_human_review_gateway
→ delivery_ready
```

Postgres remains the source of truth for jobs, assets, outputs, tasks, events, errors, approvals, client profiles, and messages. Google Drive remains the workspace/file layer. GitHub remains the source of truth for workflow JSON; n8n is runtime only.

## Safety gates retained

- Request analysis approval gate.
- Content plan approval gate.
- Final delivery approval gate with `reviewer_type='human'` metadata.
- Agent gateway boundaries that block destructive, publishing, credential, schema, direct workflow-edit, and final-approval actions.
- Dry-run payloads for sandbox testing before live LLM/Drive execution.

## Import rule

Import only the active operator build:

```bash
bash scripts/validate_repo.sh
python scripts/static_workflow_audit.py
python scripts/pre_n8n_readiness_check.py
bash scripts/n8n_import_preflight.sh
```

`scripts/n8n_import_preflight.sh` targets `workflows/active/`. If the n8n CLI is unavailable, the script exits honestly after the repository-side checks.

## Documentation

- `docs/architecture.md` — operator workflow architecture and status lifecycle.
- `docs/tool_registry.md` — human-readable callable tool registry.
- `schemas/tool_registry.schema.json` and `examples/tool_registry.example.json` — machine-readable registry contract.
- `docs/deployment_model.md` — GitHub-to-n8n deployment model.
- `docs/setup_guide.md` — setup/import sequence.
- `docs/credential_mapping.md` — required credentials.
- `docs/failure_recovery.md` — retry, pause, resume, and rollback guidance.
- `tests/sandbox_test_plan.md` — first sandbox test path.

## Not live-tested in this repo

Repository validation does not prove n8n runtime execution, credential attachment, Postgres connectivity, Google Drive OAuth actions, OpenAI/LiteLLM responses, supervisor callbacks, or notification delivery. Those must be verified in an n8n sandbox.
