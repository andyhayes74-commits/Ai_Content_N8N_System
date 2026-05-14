# AI Content n8n System v2 Build Roadmap

**Reference:** `docs/system_source_of_truth.md`  
**Purpose:** Turn the development plan into an actionable implementation roadmap.  
**Status:** Roadmap

---

## Roadmap Overview

The system should move from a working fixed-path v1 automation to a modular v2 platform in controlled releases.

```text
v1.0 baseline
-> v2.1 registry and planner awareness
-> v2.2 plan-driven orchestration
-> v2.3 policy approvals
-> v2.4 QA repair
-> v2.5 client profiles
-> v2.6 asset modules
-> v2.7 specialist tools
-> v3.0 production-ready platform
```

Each release must preserve the current working pipeline unless the replacement path has already passed dry-run and live tests.

---

## Release v1.1: Baseline Hardening

**Objective:** Lock in the working state.

### Build Items

- Replace temporary `AI_AGENT_WEBHOOK_AUTH` value with permanent operator token.
- Add a baseline smoke-test script or documented test command.
- Store expected dry-run response details.
- Confirm all active n8n workflow changes are in GitHub.
- Add README link to `docs/system_source_of_truth.md`.
- Document current limitations clearly.

### Checks

- Deploy action succeeds.
- Active workflow check passes.
- Dry-run orchestrator test returns `200 OK`.
- Supervisor `check_status` returns the test job.
- No open errors for baseline job.

### Exit Criteria

The current system can be redeployed and retested without manual workflow edits.

---

## Release v2.1: Tool Registry And Planner Awareness

**Objective:** Make the planner aware of active tools.

### Build Items

- Create `registry/tools.active.json`.
- Create optional placeholder files:
  - `registry/tools.disabled.json`
  - `registry/tools.experimental.json`
- Expand `schemas/tool_registry.schema.json`.
- Register current callable tools.
- Mark gateway/orchestrator workflows as infrastructure.
- Add registry validation script.
- Add CI/local validation to `scripts/validate_repo.sh`.
- Update `tool_content_planning` to receive or load `available_tools`.
- Update planner prompt to only select registered active tools.
- Store `tool_execution_plan` in `content_outputs`.
- Add dry-run planner test payloads.

### Checks

- Registry schema validates.
- Every active tool maps to `workflows/active/`.
- Every active workflow is registered or infrastructure-only.
- Planner output includes:
  - `selected_tools`
  - `execution_order`
  - `missing_inputs`
  - `missing_capabilities`
  - `approval_policy`
- Planner does not invent tools.

### Exit Criteria

The planner can produce a registry-backed plan while the old fixed path still works.

---

## Release v2.2: Plan-Driven Orchestration

**Objective:** Execute tools selected by the planner.

### Build Items

- Add plan reader workflow or code node.
- Add selected-tool validation.
- Add `plan_driven` mode.
- Keep `legacy_fixed_path` mode.
- Record each tool execution in `content_tasks`.
- Add failure classification in `content_errors`.
- Add retry route for retryable tool failures.
- Add tests for:
  - valid selected tools
  - disabled tool rejection
  - missing capability block
  - skipped optional step

### Checks

- Stored plan can drive execution order.
- Tool IDs are validated against registry.
- Disabled/deprecated tools cannot run by default.
- Tool run state is visible in Postgres.

### Exit Criteria

A dry-run job can execute selected tools from a stored plan.

---

## Release v2.3: Approval Policy Engine

**Objective:** Make approvals configurable.

### Build Items

- Add approval policy handling:
  - `none`
  - `qa_only`
  - `operator_final`
  - `full_staged`
  - `client_review_required`
- Add policy to planner output.
- Add policy evaluation in orchestrator or approval layer.
- Update human review gateway to respect policy.
- Add tests for each policy.
- Keep final human approval protection where policy requires it.

### Checks

- `none` policy can run without staged approval in dry-run.
- `full_staged` still blocks at analysis, plan, and final gates.
- Human-only gates cannot be satisfied by agent/system actions.

### Exit Criteria

Approval behaviour is driven by job/client policy instead of only hardcoded workflow gates.

---

## Release v2.4: QA And Repair Loop

**Objective:** Repair safe output issues automatically.

### Build Items

- Expand QA report schema.
- Add `tool_repair_output`.
- Add repair attempt records.
- Add max repair attempts.
- Add repair routes for:
  - JSON repair
  - missing fields
  - tone mismatch
  - unsupported claims
  - formatting
  - length limits
- Add final escalation to human review.

### Checks

- QA issues are structured.
- Repair attempts are logged.
- Successful repair updates output state.
- Failed repair escalates cleanly.

### Exit Criteria

QA can repair known safe issues and preserve a full repair audit trail.

---

## Release v2.5: Client Profile Rules

**Objective:** Make jobs client-aware.

### Build Items

- Expand client profile model.
- Add client rules for:
  - tone
  - brand voice
  - approved claims
  - forbidden claims
  - output defaults
  - approval defaults
  - delivery preferences
- Feed client profile into planner, generation, QA, and delivery.
- Add demo client tests.

### Checks

- Different clients can produce different plan constraints.
- Forbidden claims are caught.
- Client approval policy can override planner recommendation.

### Exit Criteria

Client profile data has visible impact on planning and QA.

---

## Release v2.6: Asset Module System

**Objective:** Reuse and pre-render client/product assets.

### Build Items

- Define asset module schema.
- Add `content_asset_modules` migration.
- Add `tool_asset_pre_renderer`.
- Add `tool_product_module_selector`.
- Add registry entries for new asset tools.
- Add dry-run asset module tests.
- Feed selected modules into planning and generation.

### Checks

- Asset modules can be created and indexed.
- Planner can see available asset modules.
- Jobs can reuse modules instead of reprocessing assets.

### Exit Criteria

Reusable asset modules can influence a job plan and outputs.

---

## Release v2.7: Specialist Content Tools

**Objective:** Split broad generation into focused tools.

### Build Items

Build specialist tools gradually:

- `tool_generate_social_posts`
- `tool_generate_blog_article`
- `tool_generate_email_campaign`
- `tool_generate_image_briefs`
- `tool_generate_video_script`
- `tool_qa_claim_checker`
- `tool_qa_brand_checker`
- `tool_delivery_packager`

For each tool:

- Add workflow JSON.
- Add registry entry.
- Define input and output contract.
- Add dry-run support.
- Add validation.
- Add docs.
- Run live test before production use.

### Checks

- Planner selects specialist tools when appropriate.
- Generic generation remains available as fallback.
- Specialist output is stored consistently.

### Exit Criteria

Common content jobs are handled by specialist registered tools.

---

## Release v3.0: Production-Ready Platform

**Objective:** Prepare for repeated real client operation.

### Build Items

- Add live test suite.
- Add credential health checks.
- Add Postgres migration checks.
- Add Drive upload/download tests.
- Add LLM call tests.
- Add approval flow tests.
- Add delivery pack tests.
- Add rollback procedure.
- Add monitoring and alerting.
- Add backup/export procedure.
- Finalize operator manual.
- Add release checklist per version.

### Checks

- Fresh deploy works.
- Smoke test works.
- Full dry-run lifecycle works.
- Live limited test works.
- Errors are visible and recoverable.
- Delivery pack is inspectable and traceable.

### Exit Criteria

The platform can be used repeatedly with real jobs, real credentials, approvals, Drive, LLM, and delivery outputs.

---

## Workstream View

| Workstream | Main Releases |
|---|---|
| Deployment and runtime stability | v1.1, v3.0 |
| Tool registry | v2.1 |
| Planner | v2.1, v2.2 |
| Orchestrator | v2.2 |
| Approvals | v2.3 |
| QA and repair | v2.4 |
| Client rules | v2.5 |
| Asset modules | v2.6 |
| Specialist tools | v2.7 |
| Delivery and operations | v3.0 |

---

## Immediate Next Sprint

The next sprint should build v2.1.

### Sprint Tasks

1. Create `registry/tools.active.json`.
2. Register the seven current callable tools.
3. Mark infrastructure workflows separately.
4. Expand `schemas/tool_registry.schema.json`.
5. Add registry validation.
6. Wire registry validation into `scripts/validate_repo.sh`.
7. Update `tool_content_planning` prompt and input shape.
8. Store planner output as `tool_execution_plan`.
9. Add dry-run planner test.
10. Update docs.

### Sprint Demo

Run a dry-run job where the planner produces a tool-aware plan and stores it in Postgres. The plan must include selected tools from the registry and must not invent unavailable tools.

