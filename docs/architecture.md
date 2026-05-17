# Operator Workflow Architecture

## Summary

The system uses one main orchestrator plus nine callable/API workflows. The active import set is intentionally small enough for operators to reason about while supporting a registry-aware, plan-driven v3 platform foundation.

## Active workflow count

- Previous debug build: 40 workflow JSON files, archived at `workflows/archive/v1_debug_build/`.
- New active build: 10 workflow JSON files in `workflows/active/`.

## Main orchestrator

`ai_content_orchestrator` receives an operator/supervisor handoff and calls the tool workflows with n8n Execute Workflow nodes. It coordinates intake, Drive workspace setup, asset scanning/indexing, request analysis, approval gates, content planning, output generation, QA, repair auditing, human review, and delivery-pack generation.

## Callable tools

- `tool_job_intake`: content job creation, inbound message registration, client profile creation/update, existing/new Drive folder handoff.
- `tool_drive_assets`: project folder creation, folder structure, Drive scan, document/image/audio-video reference handling, asset index output, reusable asset module context.
- `tool_request_analysis`: LLM analysis and `waiting_for_analysis_approval` transition.
- `tool_content_planning`: requires analysis approval where policy demands it, creates registry-aware plans, stores selected tools and asset/client context, transitions to `waiting_for_plan_approval`.
- `tool_content_generation`: requires plan approval, dispatches output types, stores generated outputs and tasks.
- `tool_qa_delivery`: QA checks, unsupported-claim/missing-info flags, safe repair attempt auditing, `waiting_for_human_review`, final approval policy check, delivery pack.
- `tool_logging`: progress events, errors, retry-safe markers.
- `api_supervisor_gateway`: external agent/supervisor API entry point.
- `api_human_review_gateway`: human-only approvals and revision decisions.


## Orchestrator routing and state handoff

Public webhook entry points authenticate with n8n header-auth credentials. The orchestrator computes an action route and passes forward `job_id`, `mode`, `action`, `payload`, `desired_tools`, `tool_results`, `current_stage`, `status`, and error metadata. Tool workflows are internal Execute Workflow targets and no-op when they are not selected for the current action, so targeted actions do not run inappropriate lifecycle stages.

Supported route groups:

| Action | Tool sequence |
|---|---|
| `create_job` / `run_lifecycle` | intake, Drive assets, request analysis; then stop for analysis approval |
| `dry_run_full_lifecycle` | dry-run operator path across all tools for sandbox validation |
| `generate_plan` | content planning, guarded by analysis approval |
| `generate_outputs` | content generation, guarded by plan approval |
| `qa_delivery` | QA and delivery, guarded by final human approval before delivery-ready |
| `run_plan` / `continue_plan` | load latest stored active tool plan and execute selected tools |
| `log_progress`, `report_error`, `retry`, `pause`, `resume`, `cancel` | logging/retry-safe tracking |

LLM tools parse OpenAI/LiteLLM `choices[0].message.content` before inserting rows into `content_outputs`. Parse warnings are recorded in `content_errors`.

## v3 platform tables

In addition to the original operational tables, the platform now uses:

- `content_job_tool_plans` for stored registry-aware plans.
- `content_job_tool_runs` for plan/tool run state.
- `content_repair_attempts` for QA repair audit trails.
- `content_asset_modules` for reusable client/product asset context.
- expanded `client_profiles` fields for brand voice, tone rules, claims, output defaults, approval defaults, asset roots, and delivery preferences.

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

Specialist tools are first registered in `registry/tools.experimental.json`, documented in `docs/specialist_tools.md`, and promoted only after they have workflow JSON, n8n workflow IDs, validation, dry-run tests, and a limited live test. The transitional fallback remains `tool_content_generation` until specialist tools are proven.
