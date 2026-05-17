# Failure Recovery

## Source of truth

Use Postgres job state and audit tables first. n8n execution history is runtime evidence, but Postgres remains the source of truth.

## Common operator actions

| Situation | Recovery |
|---|---|
| Tool execution fails before a gate | Inspect `content_errors`, correct payload/credential issue, then retry through `api_supervisor_gateway` with `action: "retry"`. |
| Job should stop temporarily | Use supervisor `pause`; set/confirm `content_jobs.status = paused`. |
| Job should resume | Use supervisor `resume`; continue from the last approved gate. |
| Request analysis needs changes | Human reviewer submits `revision_requested` for `analysis`; rerun `tool_request_analysis`. |
| Content plan needs changes | Human reviewer submits `revision_requested` for `plan`; rerun `tool_content_planning`. |
| QA flags unsupported claims | Revise inputs or regenerate affected outputs; do not advance final approval until QA and human review pass. |
| QA flags repairable issues only | Inspect `content_repair_attempts`; if attempts are completed and no blocking issues remain, `qa_only` jobs may continue to delivery. |
| QA repair fails or exceeds attempts | Keep the job in `waiting_for_human_review`, inspect `content_repair_attempts.error_message`, then revise or regenerate affected outputs. |
| Planner selects the wrong active tool | Inspect `content_job_tool_plans.plan_payload`, correct registry/planner context, regenerate the plan, then rerun `run_plan`. |
| Asset context is stale | Re-run the Drive asset step, confirm `content_asset_modules.updated_at`, then regenerate the plan. |
| Delivery pack generated incorrectly | Keep the generated output for audit, create a corrected generation route, and require final human approval again. |

## Retry-safe policy

`tool_logging` records retry context and uses the marker `retry_count < max_retries`. Retries must not skip approval gates.

## Rollback

Preferred rollback is to redeploy the last known good GitHub commit through the deploy action. If the operator build cannot be used, the archived v1 debug build in `workflows/archive/v1_debug_build/` remains a reference fallback. Keep `workflows/active/` as the normal import target after rollback analysis is complete.

## Production smoke recovery

If `scripts/production_smoke_test.mjs` fails:

- inspect the failing action in the script output,
- check recent n8n executions,
- inspect `content_errors`,
- verify credential names still exist in n8n,
- redeploy from GitHub after correcting workflow JSON.
