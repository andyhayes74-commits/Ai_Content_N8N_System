# AI Content n8n System v2 Development Plan

**Reference:** `docs/system_source_of_truth.md`  
**Purpose:** Define the development plan for taking the current activated v1 pipeline to the finished modular product described in the source-of-truth brief.  
**Status:** Planning document

---

## 1. Current Baseline

The current system is a working transitional v1 pipeline:

- GitHub deploys workflow JSON to n8n.
- n8n is the runtime.
- Postgres stores jobs, outputs, events, approvals, assets, tasks, and errors.
- Google Drive and LLM credentials are configured through n8n credentials.
- The orchestrator can run a dry-run job through intake, assets, and request analysis.
- The first approval gate is reached at `waiting_for_analysis_approval`.

This is useful, but it is not the finished architecture. The source-of-truth brief defines the target as a modular, tool-aware, client-aware, asset-aware content production platform.

---

## 2. Target Product

The finished system should behave like a reusable content production engine:

```text
Job request
-> classify the job
-> inspect available tools
-> inspect client/profile/assets
-> create a tool-aware execution plan
-> run selected tools
-> QA and repair
-> approval handling
-> delivery packaging
-> record everything
```

The most important architectural shift is moving from a fixed pipeline to a registry-driven planning and execution model.

---

## 3. Development Principles

Future development must follow these rules:

- GitHub remains the source of truth for workflow JSON, scripts, schemas, and docs.
- n8n remains runtime only.
- Postgres remains the operational source of truth.
- Credentials stay in n8n credentials only.
- Tools must be registered before the planner can select them.
- The planner must not invent tools.
- Missing capabilities must be recorded honestly.
- Approval gates must become policy-driven.
- QA should repair safe issues before escalating to humans.
- The current working pipeline must remain usable while v2 is introduced.

---

## 4. Phase 1: Stabilize Current v1

**Goal:** Keep the current activated system reliable while v2 is built.

### Deliverables

- Confirm all live n8n workflow fixes are exported to GitHub.
- Keep GitHub-to-n8n deployment working.
- Keep Postgres schema setup documented.
- Replace the temporary webhook auth token with a permanent operator token.
- Preserve the baseline dry-run payload and expected result.
- Update README or setup docs to point to the source-of-truth brief.
- Mark the current workflow chain as the transitional basic pipeline.

### Definition Of Done

- `ai_content_orchestrator` returns `200 OK` for a dry-run job.
- The job reaches `waiting_for_analysis_approval`.
- Supervisor `check_status` works.
- The baseline job has no open errors.
- A fresh deploy from GitHub reproduces the same workflow state.

---

## 5. Phase 2: Runtime Tool Registry

**Goal:** Make tools visible to the system as runtime capabilities.

### Deliverables

- Add `registry/tools.active.json`.
- Optionally add:
  - `registry/tools.disabled.json`
  - `registry/tools.experimental.json`
  - `registry/tool_categories.json`
- Expand `schemas/tool_registry.schema.json`.
- Register the current active callable tools:
  - `tool_job_intake`
  - `tool_drive_assets`
  - `tool_request_analysis`
  - `tool_content_planning`
  - `tool_content_generation`
  - `tool_qa_delivery`
  - `tool_logging`
- Mark API and webhook workflows as infrastructure-only.
- Add validation that every active tool maps to a workflow in `workflows/active/`.
- Add validation that every active workflow is either registered or explicitly infrastructure-only.
- Document the process for adding a new tool.

### Definition Of Done

- Registry validates locally and in CI.
- Every active tool has a complete registry entry.
- The planner has a clean machine-readable list of tools.
- Disabled, experimental, and deprecated tools cannot be selected by default.

---

## 6. Phase 3: Planner Awareness

**Goal:** Make planning depend on the active tool registry.

### Deliverables

- Update `tool_content_planning` to receive or load:
  - job request
  - request analysis
  - client profile
  - asset index
  - active tool registry
  - approval rules
  - known constraints
- Update the planner prompt with strict tool-selection rules:
  - select only from `available_tools`
  - do not invent tools
  - record missing capabilities
  - prefer the smallest safe tool set
  - respect client and approval rules
- Update planner output to include:
  - `job_type`
  - `summary`
  - `selected_tools`
  - `execution_order`
  - `required_inputs`
  - `missing_inputs`
  - `missing_capabilities`
  - `approval_policy`
  - `estimated_outputs`
  - `risks`
  - `planner_reasoning`
- Store the selected plan as:
  - `content_outputs.output_type = tool_execution_plan`
- Add dry-run planner tests.

### Definition Of Done

- Planner output is strict JSON.
- Planner selects only tools from the active registry.
- Unsupported requests produce `missing_capabilities`.
- The existing v1 route still works during transition.

---

## 7. Phase 4: Dynamic Execution

**Goal:** Let the orchestrator execute the selected plan rather than only a fixed route.

### Deliverables

- Add execution-plan reader.
- Add selected-tool validator.
- Add plan-driven execution mode.
- Keep legacy fixed-path mode as fallback.
- Record tool run state initially in `content_tasks`.
- Add non-breaking migrations later for:
  - `content_job_tool_plans`
  - `content_job_tool_runs`
- Add failure classification:
  - `recoverable`
  - `retryable`
  - `requires_human`
  - `blocked_missing_input`
  - `fatal`

### Definition Of Done

- A stored plan can drive tool execution.
- Each selected tool run is recorded.
- Invalid or disabled tools are rejected before execution.
- Failed tools produce useful `content_errors` records.

---

## 8. Phase 5: Policy-Driven Approvals

**Goal:** Replace hardcoded gates with configurable approval policy.

### Deliverables

- Support approval policies:
  - `none`
  - `qa_only`
  - `operator_final`
  - `full_staged`
  - `client_review_required`
- Include approval policy in planner output.
- Allow client profile rules to override planner recommendation.
- Update human review gateway to enforce policy.
- Preserve human-only approval boundaries.
- Record reviewer source:
  - `human`
  - `agent`
  - `client`
  - `system`

### Definition Of Done

- Low-risk dry-run jobs can use lighter gates.
- High-risk jobs can require full staged approval.
- Agents cannot impersonate human approval.

---

## 9. Phase 6: QA And Repair

**Goal:** Let QA repair safe issues before human review.

### Deliverables

- Expand QA report schema.
- Add `tool_repair_output`.
- Track repair attempts using existing outputs/errors first.
- Add `content_repair_attempts` later if needed.
- Support safe repair cases:
  - invalid JSON
  - missing sections
  - tone mismatch
  - unsupported claim removal
  - format correction
  - length correction
- Add max repair attempt policy.
- Escalate unresolved issues to human review.

### Definition Of Done

- QA produces structured issue records.
- Safe issues can trigger repair.
- Repair attempts are logged.
- Failed repair routes to human review or failed state.

---

## 10. Phase 7: Client Profile Rules

**Goal:** Make planning, generation, QA, and delivery client-aware.

### Deliverables

- Expand `client_profiles` or add client rules tables.
- Support:
  - brand voice
  - tone rules
  - approved claims
  - forbidden claims
  - product families
  - default outputs
  - default approval policy
  - asset roots
  - delivery preferences
  - compliance notes
- Feed client profile into:
  - request analysis
  - planning
  - generation
  - QA
  - delivery

### Definition Of Done

- Different client profiles can change plan and QA behaviour.
- Forbidden claims are caught or removed.
- Client default approval policy is respected.

---

## 11. Phase 8: Asset Module System

**Goal:** Support reusable and pre-rendered client/product assets.

### Deliverables

- Define asset module schema.
- Add `content_asset_modules`.
- Add `tool_asset_pre_renderer`.
- Add `tool_product_module_selector`.
- Store:
  - module type
  - compatibility tags
  - usage rules
  - source files
  - generated assets
  - prompt context
  - version
  - status
- Feed selected modules into planning and generation.

### Definition Of Done

- Assets can be prepared before a job.
- Jobs can reuse existing modules.
- Planner can select relevant asset modules.

---

## 12. Phase 9: Specialist Tools

**Goal:** Replace broad generic generation with focused production tools.

Candidate tools:

- `tool_job_classifier`
- `tool_prompt_builder`
- `tool_generate_social_posts`
- `tool_generate_blog_article`
- `tool_generate_email_campaign`
- `tool_generate_image_briefs`
- `tool_generate_video_script`
- `tool_qa_claim_checker`
- `tool_qa_brand_checker`
- `tool_delivery_packager`

Each tool must include:

- workflow JSON
- registry entry
- input contract
- output contract
- required credentials
- required tables
- dry-run behaviour
- failure mode
- validation
- tests
- docs

### Definition Of Done

- Planner can select specialist tools when appropriate.
- Generic generation remains available until specialist tools are proven.
- Broad generic generation can be deprecated later, not removed early.

---

## 13. Phase 10: Delivery And Production Hardening

**Goal:** Make the system safe for repeatable client-facing operation.

### Deliverables

- Improve delivery packs.
- Include:
  - outputs
  - source assets
  - QA report
  - approval history
  - repair history
  - revision notes
  - metadata
- Support client delivery preferences.
- Add live test suite:
  - credentials
  - Postgres
  - Drive
  - LLM
  - approvals
  - delivery
- Add rollback procedure.
- Add monitoring and error review process.
- Add backup/export procedure.
- Update operator manual.

### Definition Of Done

- New deployments are repeatable.
- Failures are visible and recoverable.
- Operator can run, pause, retry, approve, and inspect jobs.
- Delivery pack is usable by a client or operator.

---

## 14. Recommended Immediate Next Work

The next development target is:

```text
v2.1 - Tool Registry and Planner Awareness
```

Do not start by building many new tools. Build the registry and planner awareness first. This creates the foundation for every later phase.

