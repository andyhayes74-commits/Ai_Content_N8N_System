# Deployment Model

## Source of truth

GitHub is the source of truth for workflow JSON, documentation, schemas, fixtures, and validation scripts. n8n is the runtime.

Operators should edit workflows in GitHub and import/deploy them to n8n. Manual n8n UI edits are allowed only for emergency runtime diagnosis and must be exported back to GitHub or discarded.

## Import target

Only import `workflows/active/`. Do not import `workflows/archive/v1_debug_build/` during normal deployment.

```bash
bash scripts/validate_repo.sh
python3 scripts/static_workflow_audit.py
python3 scripts/pre_n8n_readiness_check.py
bash scripts/n8n_import_preflight.sh
```

## GitHub Actions deployment

The manual workflow `.github/workflows/deploy-n8n.yml` can deploy the active workflow set into an existing n8n instance through the n8n public API. It follows the Ghostwriter deployment pattern: validate locally, strip runtime/read-only fields, then update known n8n workflow IDs.

It deploys these files:

- `workflows/active/ai_content_orchestrator.json`
- `workflows/active/tool_job_intake.json`
- `workflows/active/tool_drive_assets.json`
- `workflows/active/tool_request_analysis.json`
- `workflows/active/tool_content_planning.json`
- `workflows/active/tool_content_generation.json`
- `workflows/active/tool_qa_delivery.json`
- `workflows/active/tool_logging.json`
- `workflows/active/api_supervisor_gateway.json`
- `workflows/active/api_human_review_gateway.json`

The deploy script sends only:

- `name`
- `nodes`
- `connections`
- `settings`

It intentionally excludes instance/runtime fields such as `id`, `versionId`, `active`, `meta`, `tags`, `pinData`, `staticData`, timestamps, owner/share fields, and credential usage fields.

## Required GitHub secrets

Add:

| Secret | Required | Description |
|---|---:|---|
| `N8N_BASE_URL` | yes for live deploy | Base URL of the n8n instance, for example `https://n8n.example.com`. |
| `N8N_API_KEY` | yes for live deploy | n8n public API key. |
| `N8N_WORKFLOW_ID_MAP` | recommended | JSON object mapping local workflow names to existing n8n workflow IDs. |
| `N8N_DEPLOY_ACTIVE` | no | Optional boolean. Leave unset to preserve current active state. |

`N8N_WORKFLOW_ID_MAP` example:

```json
{
  "ai_content_orchestrator": "abc123",
  "tool_job_intake": "def456",
  "tool_drive_assets": "ghi789",
  "tool_request_analysis": "jkl012",
  "tool_content_planning": "mno345",
  "tool_content_generation": "pqr678",
  "tool_qa_delivery": "stu901",
  "tool_logging": "vwx234",
  "api_supervisor_gateway": "yz567",
  "api_human_review_gateway": "890abc"
}
```

Alternatively, set individual secrets:

- `N8N_WORKFLOW_ID_AI_CONTENT_ORCHESTRATOR`
- `N8N_WORKFLOW_ID_TOOL_JOB_INTAKE`
- `N8N_WORKFLOW_ID_TOOL_DRIVE_ASSETS`
- `N8N_WORKFLOW_ID_TOOL_REQUEST_ANALYSIS`
- `N8N_WORKFLOW_ID_TOOL_CONTENT_PLANNING`
- `N8N_WORKFLOW_ID_TOOL_CONTENT_GENERATION`
- `N8N_WORKFLOW_ID_TOOL_QA_DELIVERY`
- `N8N_WORKFLOW_ID_TOOL_LOGGING`
- `N8N_WORKFLOW_ID_API_SUPERVISOR_GATEWAY`
- `N8N_WORKFLOW_ID_API_HUMAN_REVIEW_GATEWAY`

## First deployment process

1. Import `workflows/placeholders/` into n8n once, or import `workflows/active/` directly if you are ready to attach credentials immediately.
2. Attach the required n8n credentials from `docs/credential_mapping.md`.
3. Copy each n8n workflow ID into `N8N_WORKFLOW_ID_MAP` or the individual ID secrets.
4. Run **Deploy AI Content workflows to n8n** from GitHub Actions with `dry_run=true`.
5. Confirm all 10 workflow names and IDs are shown correctly.
6. Run the same action with `dry_run=false`.
7. Open n8n and visually inspect the workflows before live sandbox testing.

The placeholder files are intentionally minimal and exist only to create stable n8n workflow IDs for first-time deployment. Do not use them as runtime workflows.

## Backup direction

Future n8n exports can be backed up to GitHub for comparison, but exported runtime JSON should not silently replace source files. Any differences must be reviewed as workflow drift.

## Rollback

Rollback is available by importing the archived v1 debug build from `workflows/archive/v1_debug_build/`, but the normal active import folder remains `workflows/active/`.
