# Pre-n8n Completion Report

Status: PR review required. The required PR checks cover repository validation, static audit, and pre-n8n readiness. The slower n8n CLI import preflight is available as a manual `workflow_dispatch` option because global n8n installation is heavy in GitHub Actions.

## Completed in this branch

- Added pre-n8n validation, import-preflight, and GitHub Actions guardrails.
- Updated GitHub Actions to Node 24-capable action versions: `actions/checkout@v6`, `actions/setup-python@v6`, and `actions/setup-node@v6`.
- Added `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24=true` to the workflow environment for early Node 24 opt-in.
- Fixed expression guardrails to avoid false positives on valid n8n expressions.
- Added `scripts/build_llm_workflows.py` to deterministically generate LLM workflow JSONs.
- Added `scripts/embed_llm_prompts.py` so generated LLM workflows carry embedded task-specific prompts rather than generic prompt-file pointers.
- Added `scripts/build_drive_workflows.py` to deterministically generate Google Drive-ready workflow JSONs.
- Added `scripts/fix_generated_n8n_expressions.py` to restore Python-collapsed n8n expression braces after generation.
- Adjusted `validate_repo.sh` so generated workflow expression scanning no longer scans the checker scripts themselves.
- Replaced silent `rg -q` marker checks with explicit Python marker checks so failures report the exact missing marker.
- Narrowed the committed-secret scan so it scans repo content and generated workflows, not the scanner regex code itself.
- Made the n8n CLI import preflight manual in GitHub Actions to avoid blocking PR checks on a slow global n8n install.
- Added full dry-run sandbox payload pack under `tests/payloads/`.
- Added expected database checks in `tests/expected_db_checks.sql`.
- Updated README to require clone-and-preflight import.

## Live-mode workflow structure

LLM workflows include Postgres context read, embedded task-specific prompt instructions, OpenAI/LiteLLM HTTP Request node, JSON response parsing, `content_outputs` persistence, `content_errors` failure logging, and explicit `mode='dry_run'` fallback path.

Drive workflows include Google Drive REST HTTP Request node structure, folder creation structure, subfolder creation structure, file listing structure, delivery-pack upload structure, and Postgres event/output persistence.

## Remaining live-only checks

These cannot be fully confirmed until n8n has real credentials:

- Postgres connection execution.
- Google Drive OAuth folder/file operations.
- OpenAI/LiteLLM model responses.
- Notification webhook delivery.
- OpenClaw/Hermes live callbacks.

## Manual import preflight

To run the heavier n8n CLI import check in GitHub Actions, trigger the `Pre-n8n readiness` workflow manually and choose `run_n8n_import=true`.

For local/server preflight, run:

```bash
bash scripts/n8n_import_preflight.sh
```
