# Operator Workflow Architecture

## Summary

The system now uses one main workflow plus nine callable workflows. The active import set is intentionally small enough for operators to reason about while avoiding one large fragile workflow.

## Active workflow count

- Previous debug build: 40 workflow JSON files, archived at `workflows/archive/v1_debug_build/`.
- New active build: 10 workflow JSON files in `workflows/active/`.

## Main orchestrator

`ai_content_orchestrator` receives an operator/supervisor handoff and calls the tool workflows with n8n Execute Workflow nodes. It coordinates intake, Drive workspace setup, asset scanning/indexing, request analysis, approval gates, content planning, output generation, QA, human review, and delivery-pack generation.

## Callable tools

- `tool_job_intake`: content job creation, inbound message registration, existing/new Drive folder handoff.
- `tool_drive_assets`: project folder creation, folder structure, Drive scan, document/image/audio-video reference handling, asset index output.
- `tool_request_analysis`: LLM analysis and `waiting_for_analysis_approval` transition.
- `tool_content_planning`: requires analysis approval, creates plan, transitions to `waiting_for_plan_approval`.
- `tool_content_generation`: requires plan approval, dispatches output types, stores generated outputs and tasks.
- `tool_qa_delivery`: QA checks, unsupported-claim/missing-info flags, `waiting_for_human_review`, final human approval check, delivery pack.
- `tool_logging`: progress events, errors, retry-safe markers.
- `api_supervisor_gateway`: external agent/supervisor API entry point.
- `api_human_review_gateway`: human-only approvals and revision decisions.

## Preserved statuses

The architecture preserves these statuses without replacement:

- `created`
- `intake_complete`
- `assets_scanning`
- `assets_parsed`
- `analysis_complete`
- `waiting_for_analysis_approval`
- `waiting_for_plan_approval`
- `generating_outputs`
- `qa_in_progress`
- `waiting_for_human_review`
- `delivery_ready`
- `completed`
- `failed`
- `paused`
- `cancelled`

## Source-of-truth layers

- Postgres: job state and audit trail.
- Google Drive: workspace/file layer.
- GitHub: workflow/configuration source of truth.
- n8n: runtime execution environment.

## Extension pattern

Add future output tools by extending the dispatch map in `tool_content_generation` and registering the new output contract in `docs/tool_registry.md` and `examples/tool_registry.example.json`. Intended future tools include LinkedIn posts, YouTube scripts, Canva design generation, podcast episode assets, client proposal generation, SEO briefs, image generation execution, and CapCut packaging.
