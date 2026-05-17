# Release Checklist

## Repository checks

- [ ] `bash scripts/validate_repo.sh`
- [ ] `python3 scripts/static_workflow_audit.py`
- [ ] `python3 scripts/pre_n8n_readiness_check.py`
- [ ] `bash scripts/n8n_import_preflight.sh` in an environment with n8n CLI.
- [ ] `node --check scripts/deploy-n8n-workflows.mjs`
- [ ] `DRY_RUN=true node scripts/deploy-n8n-workflows.mjs`

## Import checks

- [ ] Import only `workflows/active/`.
- [ ] Confirm exactly 10 active operator workflows are present in n8n.
- [ ] Confirm archived v1 debug workflows were not imported unless intentionally rolling back.
- [ ] Add `N8N_BASE_URL`, `N8N_API_KEY`, and workflow ID mapping secrets in GitHub.
- [ ] Run **Deploy AI Content workflows to n8n** with `dry_run=true`.
- [ ] Run **Deploy AI Content workflows to n8n** with `dry_run=false`.

## Sandbox checks

- [ ] Run `tests/payloads/01_orchestrator_dry_run_job.json`.
- [ ] Run `tests/payloads/07_qa_repair_dry_run.json` after creating a test job and plan.
- [ ] Run `tests/payloads/08_asset_module_planner_dry_run.json`.
- [ ] Run supervisor status check.
- [ ] Run analysis, plan, and final human approval paths.
- [ ] Run one generation route.
- [ ] Run QA/delivery route.
- [ ] Execute `tests/expected_db_checks.sql`.

## Production readiness

- [ ] Run `node scripts/production_smoke_test.mjs` with `N8N_BASE_URL`, `N8N_API_KEY`, and `AI_AGENT_WEBHOOK_AUTH` supplied by secrets.
- [ ] Postgres credential execution verified.
- [ ] Google Drive OAuth actions verified with test folder.
- [ ] OpenAI/LiteLLM responses verified.
- [ ] Supervisor callbacks verified.
- [ ] Notification delivery verified.
- [ ] Human operator signs off final approval gate behavior.
- [ ] Confirm `docs/v3_production_runbook.md` rollback and backup steps are current.
