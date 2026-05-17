# Tool Registry

All callable workflows accept JSON and return JSON. Public API entry points use n8n header-auth credentials; callable tool workflows are internal Execute Workflow targets. Agent-safe means callable by the supervisor gateway within the documented safety boundaries.

Machine-readable runtime registry files now live in:

- `registry/tools.active.json`
- `registry/tools.disabled.json`
- `registry/tools.experimental.json`
- `registry/infrastructure_workflows.json`

`registry/tools.active.json` is runtime context for the planner. It is not only documentation. The planner must select tools only from active registry entries and must record unavailable needs as `missing_capabilities`. Experimental tools are documented contracts only until promoted.

Validation is handled by:

```bash
python3 scripts/validate_tool_registry.py
```

| Workflow | Purpose | Input JSON contract | Output JSON contract | Tables touched | Credentials | Approval gates | Agent-safe | Human-only |
|---|---|---|---|---|---|---|---:|---:|
| `ai_content_orchestrator` | Main lifecycle controller; calls tool workflows with Execute Workflow nodes. | `{job_id?, action?, mode?, payload?}` | `{job_id, status, lifecycle_step, tool_results?}` | Delegates to tools; logs `content_events`. | Postgres via tools, Drive via tools, LLM via tools. | Coordinates all gates. | yes | no |
| `tool_job_intake` | Create content job, register inbound messages, attach/create Drive handoff metadata. | `{external_job_ref?, project_name, brief_text, requested_outputs?, drive_folder_id?, mode?}` | `{job_id, status:intake_complete}` | `content_jobs`, `job_messages`, `content_events`, `client_profiles` read/reference. | Postgres. | none. | yes | no |
| `tool_drive_assets` | Create project folder/structure, scan Drive assets, parse/summarise docs, describe images, placeholder audio/video handling, create asset index and reusable asset module context. | `{job_id, drive_folder_id?, mode?}` | `{job_id, status:assets_parsed, asset_index, asset_module?}` | `content_jobs`, `content_assets`, `content_outputs`, `content_asset_modules`, `content_events`. | Postgres, Google Drive. | none. | yes | no |
| `tool_request_analysis` | Analyse client request and store analysis. | `{job_id, mode?, fallback_payload?}` | `{job_id, output_type:request_analysis, status:waiting_for_analysis_approval}` | `content_jobs`, `content_outputs`, `content_events`, `content_errors`. | Postgres, OpenAI/LiteLLM. | Opens analysis approval gate. | yes | no |
| `tool_content_planning` | Generate a registry-aware tool execution plan using active tools plus client profile and asset module context. | `{job_id, mode?, available_tools?, request_analysis?, client_profile?, asset_modules?}` | `{job_id, output_type:tool_execution_plan, selected_tools, execution_order, missing_capabilities, approval_policy, status:waiting_for_plan_approval}` | `content_jobs`, `content_outputs`, `content_approvals`, `content_events`, `content_job_tool_plans`, `content_asset_modules`. | Postgres, OpenAI/LiteLLM. | Policy-controlled analysis gate; opens plan approval gate where required. | yes | no |
| `tool_content_generation` | Dispatch and generate campaign plans, social posts, email copy, blog/article copy, image prompts, and video scripts. | `{job_id, requested_outputs?, mode?, fallback_payload?}` | `{job_id, generated_outputs:[...]}` | `content_jobs`, `content_tasks`, `content_outputs`, `content_approvals`, `content_events`. | Postgres, OpenAI/LiteLLM. | Requires plan approval. | yes | no |
| `tool_qa_delivery` | QA-check outputs, flag unsupported claims/missing information, record safe repair attempts, open human review when needed, and generate delivery pack. | `{job_id, mode?, final_approval?, qa_report?}` | `{job_id, status:waiting_for_human_review|delivery_ready, qa_report?, delivery_pack?, repair_attempt_count?}` | `content_jobs`, `content_outputs`, `content_approvals`, `content_events`, `content_errors`, `content_repair_attempts`. | Postgres, OpenAI/LiteLLM, Google Drive. | Policy-controlled final gate; human-only where policy requires it. | partial | no |
| `tool_logging` | Log progress/errors and mark retry-safe failed steps. | `{job_id, event_type?, message?, error_code?, error_message?, retry_count?}` | `{job_id, retry_safe?, logged:true}` | `content_events`, `content_errors`. | Postgres. | none. | yes | no |
| `api_supervisor_gateway` | External webhook/API entry for create job, submit message, attach Drive folder, status, active jobs, progress, errors, approval status handoff, revisions, retry, pause, resume, cancel; approval decisions route through the human gateway. | `{action, job_id?, payload?}` | `{ok, action, job_id?, status?}` | Routes to tools; may read `content_jobs`. | Postgres, inherited tool credentials. | Enforces agent boundaries; final approval blocked. | yes | no |
| `api_human_review_gateway` | Human approval actions: analysis approval, plan approval, final delivery approval, revision requests. | `{job_id, approval_stage, decision, reviewer_name?, notes?}` | `{job_id, approval_stage, decision}` | `content_approvals`, `content_jobs`, `content_events`. | Postgres. | Human-only approval gate. | no | yes |

## Database note

The core tables are preserved. A non-breaking migration adds `content_approvals.reviewer_type` so final approval can be queried explicitly as human approval.

Later non-breaking migrations add:

- `content_job_tool_plans`
- `content_job_tool_runs`
- `content_repair_attempts`
- `content_asset_modules`
- expanded client profile rule fields

## Experimental specialist tools

`registry/tools.experimental.json` contains contracts for future specialist tools such as social posts, blog articles, email campaigns, image briefs, video scripts, claim checking, brand checking, and delivery packaging. These are not active planner-selectable tools until promoted according to `docs/specialist_tools.md`.


## Auth and response parsing requirements

Every public webhook workflow that receives agent or operator input must use the `AI_AGENT_WEBHOOK_AUTH` n8n credential. Callable tool workflows must not require repo-stored secrets.

LLM-backed tools must parse OpenAI/LiteLLM chat-completion responses before storage. The expected path is `choices[0].message.content`; parsed JSON is stored in the workflow-specific `*_json` field, and parse warnings are logged to `content_errors`.

## Orchestrator action routing

`ai_content_orchestrator` passes `desired_tools`, `tool_results`, `current_stage`, `payload`, `status`, and error metadata to callable workflows. Tools that are not selected for an action return a skipped result instead of running the stage.
