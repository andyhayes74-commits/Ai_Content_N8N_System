# Current Baseline

Date: 2026-05-05

## Branches

- `main`: v1.0 RC sandbox baseline.
- `chatgpt/pre-n8n-completion-hardening`: active branch for completing the system before transfer to n8n.

## Current decision

The current `main` branch is useful, but it should not be imported into n8n as the final system yet. It is database-backed, but key model and Google Drive workflows still need live-node wiring and import preflight checks before the system leaves GitHub.

## Target for the active branch

The active branch should become the `v1.0 RC pre-n8n transfer baseline`, meaning:

- model workflows include OpenAI/LiteLLM HTTP nodes,
- Drive workflows include Google Drive or credential-ready HTTP nodes,
- validation catches dry-run-only workflows,
- n8n import preflight exists,
- payload fixtures and credential mapping are complete,
- docs state exactly what remains live-only.
