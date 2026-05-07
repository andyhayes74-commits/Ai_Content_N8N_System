# Sandbox Test Plan

This plan validates the operator-ready architecture in an n8n sandbox. It does not prove production readiness.

## Header required for every webhook call

```text
x-agent-secret: <AGENT_WEBHOOK_SECRET>
```

## Payload sequence

Use files in `tests/payloads/`:

1. `01_orchestrator_dry_run_job.json` → POST to `v1/orchestrator` for one dry-run lifecycle handoff.
2. Copy returned `job_id` into later payloads when the sandbox creates a real UUID.
3. `02_supervisor_status_check.json` → POST to `v1/supervisor` for one supervisor API status check.
4. `03_human_analysis_approval.json` → POST to `v1/human-review` for an approval flow.
5. `04_generation_route.json` → call `tool_content_generation` through the orchestrator/gateway path for one generation route.
6. `05_qa_delivery_route.json` → run QA/delivery route and confirm it stops at human review unless final approval exists.

## Expected DB checks

Run `tests/expected_db_checks.sql` after replacing `:job_id` with the sandbox job UUID.

Expected records:

- `content_jobs` has the job and reaches `waiting_for_human_review` before final approval, then `delivery_ready` after final human approval.
- `content_assets` contains the Drive workspace/index placeholder or scanned files.
- `content_outputs` contains `asset_index`, `request_analysis`, `content_plan`, at least one generated output, `qa_report`, and eventually `delivery_pack`.
- `content_tasks` contains at least one completed generation dispatch task.
- `content_events` contains approval-gate events.
- `content_approvals` contains human `analysis`, `plan`, and `final_delivery` decisions when the full approval path is tested.
- `content_errors` has no unresolved critical rows.

## Live-mode follow-up

After the dry-run path passes, repeat selected analysis, planning, generation, QA, and Drive actions in live mode using test-only assets and credentials.
