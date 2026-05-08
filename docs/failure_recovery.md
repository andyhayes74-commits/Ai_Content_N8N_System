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
| Delivery pack generated incorrectly | Keep the generated output for audit, create a corrected generation route, and require final human approval again. |

## Retry-safe policy

`tool_logging` records retry context and uses the marker `retry_count < max_retries`. Retries must not skip approval gates.

## Rollback

If the operator build cannot be used, import the archived v1 debug build from `workflows/archive/v1_debug_build/`. Keep `workflows/active/` as the normal import target after rollback analysis is complete.
