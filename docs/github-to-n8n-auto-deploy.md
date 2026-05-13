# GitHub-to-n8n auto deployment

## Purpose

GitHub remains the source of truth for the active AI Content n8n workflow set in:

```text
workflows/active/
```

The deployment system validates the repository, reads every active workflow JSON file, removes n8n read-only/runtime fields, then creates or updates matching workflows in the self-hosted n8n instance through the n8n public API.

This is adapted from the Ghostwriter n8n deployment pattern, but this repository deploys a multi-workflow operator set rather than one workflow file.

## Deployment behaviour

The deploy script is:

```text
scripts/deploy-active-workflows.mjs
```

It performs these steps:

1. Reads all `*.json` files in `workflows/active/`.
2. Validates required deployable fields: `name`, `nodes`, `connections`, and `settings`.
3. Fails if duplicate active workflow names are found.
4. Uses the n8n API to list existing workflows.
5. Matches existing workflows by stable workflow `name`.
6. Updates matched workflows with `PUT /api/v1/workflows/{id}`.
7. Falls back once to `PATCH /api/v1/workflows/{id}` if PUT returns HTTP 405.
8. Creates missing workflows with `POST /api/v1/workflows`.
9. Optionally activates or deactivates workflows only through the dedicated activation endpoints.

## Update payload

The script sends a strict update payload containing only:

```text
name
nodes
connections
settings
```

The script intentionally removes these fields from update/create payloads when present:

```text
id
versionId
active
meta
createdAt
updatedAt
triggerCount
shared
ownedBy
homeProject
usedCredentials
tags
pinData
staticData
```

This avoids overwriting instance-specific n8n runtime metadata, credentials, ownership, active state, tags, pinned data, or static execution state.

## GitHub Action

The workflow file is:

```text
.github/workflows/deploy-n8n.yml
```

It supports two modes.

### Manual dry run

Run the action manually from GitHub Actions with:

```text
dry_run=true
```

This validates the active workflows and prints what would be deployed. No n8n API calls are made.

### Manual live deploy

Run the action manually with:

```text
dry_run=false
```

This validates the repo and deploys all active workflows to n8n.

### Automatic deploy on merge to main

The action also runs automatically on pushes to `main` when relevant files change:

```text
workflows/active/**
scripts/deploy-active-workflows.mjs
scripts/validate_repo.sh
scripts/static_workflow_audit.py
scripts/pre_n8n_readiness_check.py
.github/workflows/deploy-n8n.yml
```

Automatic deploys run with `DRY_RUN=false`, so do not merge workflow changes to `main` until the target n8n instance and repository secrets are configured.

## Required GitHub secrets

Add these repository secrets before live or automatic deployment:

| Secret | Required | Description |
| --- | --- | --- |
| `N8N_BASE_URL` | Yes | Base URL for the self-hosted n8n instance, for example `https://n8n.hayfam.co.uk`. |
| `N8N_API_KEY` | Yes | n8n API key used for workflow list/create/update calls. |
| `N8N_DEPLOY_ACTIVE` | No | Optional boolean. Leave unset normally. If set, every deployed workflow is activated or deactivated after create/update. |

## First-time rollout checklist

1. Confirm `workflows/active/` contains only the operator-ready active workflows.
2. Add GitHub repository secrets `N8N_BASE_URL` and `N8N_API_KEY`.
3. Normally leave `N8N_DEPLOY_ACTIVE` unset so existing active states are not changed.
4. Run **Deploy active AI content workflows to n8n** manually with `dry_run=true`.
5. Confirm the action reports all expected active workflow names.
6. Run manually with `dry_run=false`.
7. Open n8n and confirm the workflows were created or updated by name.
8. Attach required n8n credentials from `docs/credential_mapping.md`.
9. Run the sandbox test plan in `tests/sandbox_test_plan.md`.
10. Only then rely on automatic deployment from `main`.

## Safety notes

- Do not commit n8n API keys or secrets.
- Do not manually edit active workflows in n8n without exporting and reviewing the drift against GitHub.
- Do not import `workflows/archive/v1_debug_build/` during normal deployment.
- This deploy system updates workflow definitions only. It does not prove live credentials, Postgres, Drive, LLM, supervisor, or notification execution.
- Production readiness still requires the sandbox lifecycle tests to pass with real test credentials.
