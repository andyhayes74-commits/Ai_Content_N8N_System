# Placeholder n8n Workflows

Use these files only for first-time n8n setup when the target workflows do not exist yet.

Import the files in this folder into n8n, then copy each generated n8n workflow ID into the GitHub deployment secret `N8N_WORKFLOW_ID_MAP`.

After the IDs are mapped, run the GitHub Action:

```text
Deploy AI Content workflows to n8n
```

Run with `dry_run=true` first, then `dry_run=false`.

These placeholders are intentionally minimal. The deploy action will replace their `nodes`, `connections`, and `settings` with the real workflows from `workflows/active/`.
