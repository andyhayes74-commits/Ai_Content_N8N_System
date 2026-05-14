# AI Content n8n System

**Version:** v3 production-ready platform foundation  
**Status:** Deployed and dry-run smoke-tested on n8n. Ready for repeated dry-run operation and controlled live testing after permanent credentials/tokens are confirmed.

This repository is the GitHub source of truth for a database-backed n8n automation that runs AI-assisted content jobs. n8n is the runtime only; workflow JSON, schemas, migrations, registry files, tests, and docs live here.

## What The System Does

The system accepts a client/job brief, prepares Drive/asset context, analyzes the request, creates a registry-aware execution plan, runs selected tools, performs QA and safe repair auditing, handles policy-driven approvals, and records delivery-pack metadata.

```text
Job request
-> intake
-> Drive/assets
-> request analysis
-> registry-aware planning
-> plan-driven generation
-> QA and repair audit
-> policy approval handling
-> delivery pack
```

## Active Workflows

Active workflows live only in `workflows/active/`:

1. `ai_content_orchestrator` - main lifecycle/action router.
2. `tool_job_intake` - creates/updates jobs, messages, and client profiles.
3. `tool_drive_assets` - prepares Drive asset context and reusable asset modules.
4. `tool_request_analysis` - analyzes the request and opens/records the analysis gate.
5. `tool_content_planning` - creates registry-aware tool execution plans.
6. `tool_content_generation` - transitional broad generation tool.
7. `tool_qa_delivery` - QA, safe repair audit, final gate, and delivery pack metadata.
8. `tool_logging` - progress/error logging and retry markers.
9. `api_supervisor_gateway` - operator/agent status and control gateway.
10. `api_human_review_gateway` - human approval/revision gateway.

Archived v1 debug workflows are kept under `workflows/archive/v1_debug_build/` for reference only and must not be imported during normal deployment.

## Current Capabilities

- GitHub-to-n8n deployment using workflow ID mapping.
- n8n credential-name resolution during deploy.
- Tool registry validation.
- Plan-driven orchestration using stored `content_job_tool_plans`.
- Approval policies: `none`, `qa_only`, `operator_final`, `full_staged`, and `client_review_required`.
- Client profile defaults for tone/rules/output defaults/approval policy/delivery preferences.
- Reusable asset module context in `content_asset_modules`.
- QA repair attempt auditing in `content_repair_attempts`.
- Experimental specialist tool contracts in `registry/tools.experimental.json`.
- v3 production smoke test script and manual GitHub Actions smoke workflow.

## Required n8n Credentials

Credentials are created in n8n only. Do not create env files and do not commit secrets.

- `AI_AGENT_WEBHOOK_AUTH`
- `POSTGRES_AI_CONTENT_DB`
- `GOOGLE_DRIVE_AI_CONTENT`
- `AI_LLM_HTTP_AUTH`

Important: the temporary webhook test token used during build verification must be replaced with a permanent operator token before real production use.

## Validate Locally

```bash
bash scripts/validate_repo.sh
python3 scripts/static_workflow_audit.py
python3 scripts/pre_n8n_readiness_check.py
node --check scripts/deploy-n8n-workflows.mjs
node --check scripts/production_smoke_test.mjs
```

## Deploy To n8n

Use the GitHub Action:

```text
Deploy AI Content workflows to n8n
```

Run it first with `dry_run=true`, then with `dry_run=false`.

The deploy script updates existing n8n workflow IDs. First-time installs can use `workflows/placeholders/` to create placeholder workflow IDs, then store those IDs in `N8N_WORKFLOW_ID_MAP`.

## Smoke Test

After deployment, run the manual GitHub Action:

```text
Production smoke test
```

Or run locally with secrets supplied by the shell:

```bash
N8N_BASE_URL="https://n8n.example.com" \
N8N_API_KEY="..." \
AI_AGENT_WEBHOOK_AUTH="..." \
node scripts/production_smoke_test.mjs
```

The smoke test creates a dry-run job, generates a plan, runs the plan, checks supervisor status, and verifies recent n8n executions.

## Main Documentation

- `docs/system_source_of_truth.md` - controlling product brief.
- `docs/v2_development_plan.md` and `docs/v2_build_roadmap.md` - roadmap history.
- `docs/v3_production_runbook.md` - v3 operating, rollback, and backup runbook.
- `docs/operator_manual.md` - how to run jobs and approvals.
- `docs/setup_guide.md` - setup and deployment sequence.
- `docs/deployment_model.md` - GitHub-to-n8n deployment model.
- `docs/tool_registry.md` - active and experimental tool registry notes.
- `docs/specialist_tools.md` - specialist tool promotion plan.
- `docs/credential_mapping.md` - n8n credential requirements.
- `docs/failure_recovery.md` - retry, repair, escalation, and rollback guidance.
- `docs/release_checklist.md` - release gate checklist.

## Live-Mode Note

The v3 dry-run lifecycle is verified. Before live client jobs, confirm live Google Drive upload/download, live LLM responses, permanent webhook auth, backup coverage, and operator approval behavior with test data.
