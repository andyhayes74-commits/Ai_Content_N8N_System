# Release Checklist

## Repository checks

- [ ] `bash scripts/validate_repo.sh`
- [ ] `python scripts/static_workflow_audit.py`
- [ ] `python scripts/pre_n8n_readiness_check.py`
- [ ] `bash scripts/n8n_import_preflight.sh` in an environment with n8n CLI.

## Import checks

- [ ] Import only `workflows/active/`.
- [ ] Confirm exactly 10 active operator workflows are present in n8n.
- [ ] Confirm archived v1 debug workflows were not imported unless intentionally rolling back.

## Sandbox checks

- [ ] Run `tests/payloads/01_orchestrator_dry_run_job.json`.
- [ ] Run supervisor status check.
- [ ] Run analysis, plan, and final human approval paths.
- [ ] Run one generation route.
- [ ] Run QA/delivery route.
- [ ] Execute `tests/expected_db_checks.sql`.

## Production readiness

- [ ] Postgres credential execution verified.
- [ ] Google Drive OAuth actions verified with test folder.
- [ ] OpenAI/LiteLLM responses verified.
- [ ] Supervisor callbacks verified.
- [ ] Notification delivery verified.
- [ ] Human operator signs off final approval gate behavior.
