# Deployment Model

## Source of truth

GitHub is the source of truth for workflow JSON, documentation, schemas, fixtures, and validation scripts. n8n is the runtime.

Operators should edit workflows in GitHub and import/deploy them to n8n. Manual n8n UI edits are allowed only for emergency runtime diagnosis and must be exported back to GitHub or discarded.

## Import target

Only import `workflows/active/`. Do not import `workflows/archive/v1_debug_build/` during normal deployment.

```bash
bash scripts/validate_repo.sh
python scripts/static_workflow_audit.py
python scripts/pre_n8n_readiness_check.py
bash scripts/n8n_import_preflight.sh
```

## Future GitHub Actions deployment

A future workflow can deploy by name through the n8n API:

1. Validate JSON and safety policies.
2. Read each file in `workflows/active/`.
3. Look up existing n8n workflows by stable name.
4. Update by name when found; create when missing.
5. Keep GitHub commit SHA in workflow metadata/tags.

## Backup direction

Future n8n exports can be backed up to GitHub for comparison, but exported runtime JSON should not silently replace source files. Any differences must be reviewed as workflow drift.

## Rollback

Rollback is available by importing the archived v1 debug build from `workflows/archive/v1_debug_build/`, but the normal active import folder remains `workflows/active/`.
