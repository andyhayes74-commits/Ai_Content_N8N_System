# Workflow Orchestration Map

## v2 operator flow

```text
api_supervisor_gateway / api_human_review_gateway
→ ai_content_orchestrator
→ tool_job_intake
→ tool_drive_assets
→ tool_request_analysis
→ analysis approval gate
→ tool_content_planning
→ plan approval gate
→ tool_content_generation
→ tool_qa_delivery
→ final human approval gate
→ delivery_ready
```

## Active import set

Import only `workflows/active/`. The old debug build is archived at `workflows/archive/v1_debug_build/`.

## Callable pattern

The orchestrator uses n8n Execute Workflow nodes to call tool workflows by stable workflow name. This supports future update-by-name deployment from GitHub to n8n.
