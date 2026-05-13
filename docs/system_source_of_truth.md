# AI Content n8n System - Source of Truth Brief

**Status:** Canonical development brief  
**Branch:** main  
**Purpose:** Define what this system is intended to become, how it should be built, and how all future development decisions should be judged.

---

## 1. Executive Summary

The AI Content n8n System is a standalone modular AI content production and client automation platform.

It is not a WordPress system, not a single-purpose content workflow, and not a collection of isolated n8n automations. It is intended to become a reusable production engine that can receive a client/job request, understand the available tools, plan the correct execution path, select or prepare assets, generate the required outputs, run QA, repair issues where possible, package the result, and preserve a full audit trail.

The central architectural idea is:

```text
Job request
→ classify the job
→ inspect available tools
→ inspect client/profile/assets
→ create a tool-aware execution plan
→ run the selected tools
→ QA and repair
→ package delivery
→ record everything
```

The system must be built so that new tools can be added in the future without rewriting the whole system. The planning stage must know which tools are available and must only select tools from the active tool registry. If the request needs a capability that does not exist yet, the planner must record it as a missing capability rather than inventing a fake tool.

This document is the source of truth for development. If older documentation conflicts with this brief, this brief takes priority until the older documentation is updated.

---

## 2. Product Vision

The goal is to build an AI-powered content production platform that can support many different kinds of client work, such as:

- campaign planning
- social post generation
- blog and article generation
- email copy
- product descriptions
- technical summaries
- image prompt generation
- video advert scripts
- brochure copy
- delivery packs
- asset preparation
- reusable product/module content
- pre-rendered asset chains
- future specialist tools not yet built

The system should feel less like a fixed conveyor belt and more like a modular workshop. Each job enters the system with a brief and context. The system then decides which tools are required, what assets are needed, what outputs should be produced, what checks should be run, and whether human approval is needed.

The long-term commercial value comes from the platform being reusable, expandable, and client-aware. A client should be able to have a profile, a library of assets, product/module information, rules, approved claims, tone preferences, and delivery requirements. Future tools should be plugged into the platform like new machinery on the workshop floor.

---

## 3. What This System Is

This system is:

1. **A standalone n8n-based AI content production platform.**
   n8n is the runtime and workflow execution layer.

2. **A job-driven automation engine.**
   Every content request becomes a tracked job with state, events, outputs, errors, approvals, and delivery records.

3. **A tool-aware planning system.**
   The planner must see the available tools before creating a plan.

4. **A modular execution system.**
   The system should eventually execute the tools selected by the planner rather than forcing every job through one fixed path.

5. **A client-aware production system.**
   Client profiles should influence tone, branding, approved claims, product context, approval policy, and output defaults.

6. **An asset-aware production system.**
   Assets should be indexed, described, reused, selected, and eventually pre-rendered into reusable modules.

7. **An auditable system.**
   The database must preserve what was requested, what was planned, what tools were used, what was generated, what failed, what was approved, and what was delivered.

8. **An expandable platform.**
   New tools should be addable through a defined tool registration process.

---

## 4. What This System Is Not

This system is not:

1. **A WordPress-specific system.**
   It may later be called by websites, apps, dashboards, or other systems, but it must not be designed around WordPress.

2. **A single fixed workflow.**
   The current linear content pipeline can remain as the first basic pipeline, but it must not define the long-term architecture.

3. **A generic prompt wrapper.**
   The system must do more than send a prompt to an LLM. It must manage planning, tools, assets, QA, state, and delivery.

4. **A black box with no audit trail.**
   Every important decision and output must be traceable.

5. **A system where the LLM invents capabilities.**
   The planner may only select tools that exist in the registry. Missing capabilities must be logged honestly.

6. **Production-ready by default.**
   Repository validation does not prove live n8n behaviour. Production readiness requires live execution tests with credentials, Postgres, Drive, LLM calls, approvals, and delivery flows.

---

## 5. Core Design Principles

### 5.1 Tool-aware planning first

The planning stage must be redesigned around the available tool registry. It should not assume that only campaign plans, social posts, emails, blogs, image prompts, and video scripts exist.

The planner must receive:

- job request
- request analysis
- client profile
- asset index
- active tool registry
- approval policy rules
- known constraints

The planner must output:

- job type
- selected tools
- execution order
- required inputs
- missing inputs
- missing capabilities
- approval policy
- estimated outputs
- risks
- planner reasoning

### 5.2 Tools are registered capabilities

Every callable workflow that can perform work for a job must have a registry entry. The registry must describe what the tool does, what inputs it needs, what outputs it creates, what credentials it requires, whether it is safe for agents, and when it should or should not be used.

The registry is not just documentation. It is runtime context for the planner.

### 5.3 Add tools without rewriting the system

Future tools must be added by following a repeatable process:

1. Build the callable n8n workflow.
2. Define the input and output contract.
3. Add the tool to the machine-readable registry.
4. Add or update validation.
5. Add documentation.
6. Test in dry-run mode.
7. Test in live mode.
8. Mark the tool active only when it passes.

The planner should automatically see active tools.

### 5.4 Honest missing capability handling

If the planner cannot satisfy a request with current tools, it must record missing capabilities.

Example:

```json
{
  "missing_capabilities": [
    {
      "capability": "generate_capcut_project_package",
      "reason": "No active tool can package generated assets into a CapCut project."
    }
  ]
}
```

This becomes a development signal for future tools.

### 5.5 Database as the operational source of truth

GitHub is the source of truth for code and workflow JSON. n8n is the runtime. Postgres is the operational source of truth for jobs, state, events, assets, outputs, errors, approvals, tool plans, and tool runs.

### 5.6 Human approval is configurable

Human gates are valuable, but they must not be hardcoded into every job. Different jobs need different risk levels.

Supported approval policies should include:

- `none`
- `qa_only`
- `operator_final`
- `full_staged`
- `client_review_required`

The planner should recommend an approval policy, but system rules and client profile rules may override it.

### 5.7 QA should repair, not just report

QA should not only flag issues. Where safe, the system should be able to run a repair pass before human review.

Examples:

- invalid JSON repair
- missing section repair
- tone mismatch repair
- unsupported claim removal
- format correction
- output length correction

Every repair attempt must be logged.

### 5.8 Asset reuse is a major feature

The system should support pre-rendered and reusable assets. Client/product/module assets should be stored and tagged so they can be reused across jobs.

This is especially important for clients with modular products where the final content depends on selected modules, options, models, or configurations.

---

## 6. Target Architecture

### 6.1 High-level architecture

```text
External caller or operator
→ API gateway
→ job intake
→ job classification
→ asset/context preparation
→ request analysis
→ tool-aware planner
→ execution orchestrator
→ selected tools
→ QA and repair
→ approval handling
→ delivery packaging
→ status/result API
```

### 6.2 Core layers

| Layer | Purpose |
|---|---|
| API Gateway | Accepts job requests, status checks, approvals, revisions, retries, pauses, and cancellations. |
| Job Intake | Creates or updates the tracked job record. |
| Client Profile Layer | Applies client-specific tone, brand, product, approval, and claim rules. |
| Asset Layer | Indexes, selects, parses, describes, and eventually pre-renders reusable assets. |
| Tool Registry | Defines all active, disabled, and experimental tools. |
| Planning Engine | Selects tools and creates an execution plan using the active registry. |
| Execution Orchestrator | Runs selected tools in order and records tool run state. |
| Output Layer | Stores generated outputs with structured metadata. |
| QA and Repair Layer | Checks outputs, repairs safe issues, and records quality state. |
| Approval Layer | Handles human or client decisions based on policy. |
| Delivery Layer | Creates delivery packs and final metadata. |
| Audit Layer | Stores events, errors, tool runs, plan decisions, and revisions. |

---

## 7. Tool Registry Requirements

### 7.1 Registry location

Add a machine-readable registry file:

```text
registry/tools.active.json
```

Optional future files:

```text
registry/tools.disabled.json
registry/tools.experimental.json
registry/tool_categories.json
```

### 7.2 Required fields

Each tool entry must include:

```json
{
  "tool_id": "tool_generate_social_posts",
  "workflow_name": "tool_generate_social_posts",
  "version": "1.0.0",
  "status": "active",
  "category": "content_generation",
  "description": "Generates social media posts from an approved content plan.",
  "capabilities": [
    "generate_social_posts",
    "adapt_tone_to_client_profile"
  ],
  "input_contract": {
    "job_id": "uuid",
    "client_profile": "object optional",
    "content_plan": "object",
    "requested_channels": "array optional"
  },
  "output_contract": {
    "outputs": "array",
    "output_type": "social_posts"
  },
  "required_credentials": [
    "POSTGRES_AI_CONTENT_DB",
    "AI_LLM_HTTP_AUTH"
  ],
  "required_tables": [
    "content_jobs",
    "content_outputs",
    "content_events"
  ],
  "approval_policy": "inherits_job_policy",
  "agent_safe": true,
  "human_only": false,
  "can_run_in_dry_run": true,
  "cost_level": "low",
  "average_runtime": "short",
  "failure_mode": "recoverable",
  "tags": [
    "copywriting",
    "social",
    "marketing"
  ]
}
```

### 7.3 Tool statuses

| Status | Meaning |
|---|---|
| `active` | Planner may select this tool. |
| `disabled` | Tool is documented but must not be selected. |
| `experimental` | Tool may be selected only in explicit experimental mode. |
| `deprecated` | Tool should not be used for new jobs. |

### 7.4 Planner rule

The planner must only select tools where:

```text
status = active
```

Experimental tools may only be selected when the job or operator explicitly allows experimental mode.

### 7.5 Validation rules

Validation scripts must enforce:

- every active tool points to an existing workflow in `workflows/active/`
- every active workflow has a registry entry unless it is marked as infrastructure-only
- every registry entry has required fields
- every selected tool in a stored plan exists in the registry
- no disabled or deprecated tool is selected by default
- planner prompt includes available tools

---

## 8. Planning Engine Requirements

### 8.1 Planner input

The planning workflow must receive or load:

```json
{
  "job_id": "uuid",
  "brief_text": "string",
  "requested_outputs": [],
  "client_profile": {},
  "asset_index": {},
  "request_analysis": {},
  "available_tools": [],
  "approval_rules": {},
  "mode": "dry_run|live"
}
```

### 8.2 Planner prompt rules

The LLM must be instructed:

```text
You are the planning engine for a modular AI content production system.

You may only select tools from the provided available_tools registry.
Do not invent tools.
If a needed capability does not exist, add it to missing_capabilities.
Prefer the smallest safe tool set that can complete the job.
Respect client profile rules and approval policy.
Return strict JSON only.
```

### 8.3 Planner output schema

The planner must return:

```json
{
  "job_type": "string",
  "summary": "string",
  "selected_tools": [
    {
      "tool_id": "string",
      "workflow_name": "string",
      "reason": "string"
    }
  ],
  "execution_order": [
    {
      "step": 1,
      "tool_id": "string",
      "depends_on": [],
      "required_inputs": [],
      "expected_outputs": []
    }
  ],
  "required_inputs": [],
  "missing_inputs": [],
  "missing_capabilities": [],
  "approval_policy": "none|qa_only|operator_final|full_staged|client_review_required",
  "estimated_outputs": [],
  "risks": [],
  "planner_reasoning": "string"
}
```

### 8.4 Storage

The selected plan should be stored as a structured output:

```text
content_outputs.output_type = tool_execution_plan
```

Future migrations should add a dedicated table:

```text
content_job_tool_plans
```

---

## 9. Dynamic Execution Requirements

The current orchestrator can remain as a transitional implementation, but the target system must eventually execute the planner's selected tool sequence.

### 9.1 Target execution behaviour

```text
Fetch job tool plan
→ validate selected tools against registry
→ run step 1
→ store tool run result
→ run step 2 when dependencies are satisfied
→ continue until complete or blocked
→ send to QA/repair/approval/delivery
```

### 9.2 Tool run records

Each tool execution should be recorded with:

```text
job_id
tool_id
workflow_name
step_number
status
input_payload
output_payload
started_at
completed_at
error_message
retry_count
```

Future table:

```text
content_job_tool_runs
```

### 9.3 Failure handling

Tool failures must be classified as:

- recoverable
- retryable
- requires_human
- blocked_missing_input
- fatal

The tool registry should provide a default `failure_mode`, but the runtime should record the actual failure state.

---

## 10. Client Profile Requirements

Client profiles should eventually define:

```json
{
  "client_id": "string",
  "client_name": "string",
  "brand_voice": "string",
  "tone_rules": [],
  "approved_claims": [],
  "forbidden_claims": [],
  "product_families": [],
  "default_outputs": [],
  "default_approval_policy": "operator_final",
  "asset_roots": [],
  "delivery_preferences": {},
  "compliance_notes": []
}
```

Client profile data should influence:

- planning
- tool selection
- prompt building
- QA checks
- approval policy
- delivery format

---

## 11. Asset Module System

### 11.1 Purpose

The asset module system is a future major feature. It allows reusable content and media assets to be prepared once, tagged, and reused across jobs.

This is important for clients with configurable products, product families, optional modules, model numbers, or repeating content needs.

### 11.2 Asset module fields

Asset modules should support:

```json
{
  "module_id": "string",
  "client_id": "string",
  "product_id": "string optional",
  "module_type": "image|copy|video|technical|prompt_context|rendered_asset",
  "title": "string",
  "description": "string",
  "compatibility_tags": [],
  "source_files": [],
  "generated_assets": [],
  "prompt_context": {},
  "usage_rules": {},
  "version": "string",
  "status": "active|draft|deprecated",
  "last_rendered_at": "timestamp optional"
}
```

### 11.3 Pre-rendered asset chain

The system should support a separate workflow path for preparing assets before the main job.

Example:

```text
Client uploads product files
→ asset pre-render workflow runs
→ images, descriptions, module summaries, prompt context are generated
→ reusable modules are stored
→ future content jobs select from these modules
```

This reduces repeated processing and creates a stronger client-specific production engine.

---

## 12. Specialist Tool Examples

The system should eventually support specialist tools such as:

| Tool | Purpose |
|---|---|
| `tool_job_classifier` | Classifies job type and required capabilities. |
| `tool_asset_pre_renderer` | Prepares reusable assets and module metadata. |
| `tool_product_module_selector` | Selects relevant product/module assets for a job. |
| `tool_prompt_builder` | Builds structured prompts from plan, profile, and assets. |
| `tool_generate_social_posts` | Generates platform-specific social posts. |
| `tool_generate_blog_article` | Generates long-form article content. |
| `tool_generate_email_campaign` | Generates email subject lines and email bodies. |
| `tool_generate_image_briefs` | Generates image prompts or creative briefs. |
| `tool_generate_video_script` | Generates video or advert scripts. |
| `tool_qa_claim_checker` | Checks unsupported or forbidden claims. |
| `tool_qa_brand_checker` | Checks tone and brand compliance. |
| `tool_repair_output` | Repairs format, missing sections, or QA issues. |
| `tool_delivery_packager` | Builds final delivery packs. |

These tools should be added gradually, not all at once.

---

## 13. Approval and Review Model

### 13.1 Approval policies

The system should support configurable approval policies.

| Policy | Behaviour |
|---|---|
| `none` | Runs automatically unless an error occurs. |
| `qa_only` | Runs QA and blocks only if QA fails. |
| `operator_final` | Runs automatically until final operator approval. |
| `full_staged` | Requires staged approval after analysis, plan, and final QA. |
| `client_review_required` | Requires client or external reviewer approval before delivery. |

### 13.2 Approval source

Approvals should record:

- job_id
- approval_stage
- decision
- reviewer_id
- reviewer_type
- notes
- created_at

### 13.3 Agent boundary

Agents may suggest, prepare, and request approvals, but must not impersonate human approval where human approval is required.

---

## 14. QA and Repair Model

### 14.1 QA checks

QA should check:

- JSON validity
- required fields
- output completeness
- unsupported claims
- forbidden claims
- brand/tone compliance
- missing source context
- format rules
- length limits
- duplicated content
- delivery readiness

### 14.2 Repair loop

Where safe, QA should trigger repair.

```text
Generated output
→ QA check
→ issues found
→ repair pass
→ QA re-check
→ pass or human review
```

### 14.3 Repair limits

Repair attempts should be limited by policy, for example:

```text
max_repair_attempts = 2
```

If still failing, the job should move to human review or failed state depending on severity.

---

## 15. Database Direction

The current database can be extended gradually. Avoid breaking existing tables unless necessary.

### 15.1 Existing important tables

The platform should continue using:

- `content_jobs`
- `content_assets`
- `content_tasks`
- `content_outputs`
- `content_events`
- `content_errors`
- `content_approvals`
- `client_profiles`
- `job_messages`

### 15.2 Future tables

Add when needed:

```text
content_tools
content_tool_versions
content_job_tool_plans
content_job_tool_runs
content_asset_modules
content_client_rules
content_repair_attempts
```

### 15.3 Non-breaking first step

Before adding new tables, it is acceptable to store planner outputs in `content_outputs` using clear output types:

```text
tool_execution_plan
qa_report
repair_report
asset_module_index
```

---

## 16. Development Roadmap

### Phase 1 - Source of truth and alignment

Goal: stop architecture drift.

Tasks:

- Add this source-of-truth brief.
- Update README to reference this document.
- Mark current workflows as the basic content pipeline, not the final architecture.
- Ensure future development follows this brief.

### Phase 2 - Runtime tool registry

Goal: make tools visible to the planner.

Tasks:

- Add `registry/tools.active.json`.
- Expand `schemas/tool_registry.schema.json`.
- Register all current active tools.
- Add validation scripts for registry consistency.
- Add docs for adding new tools.

### Phase 3 - Planner awareness

Goal: planning stage uses the available tool registry.

Tasks:

- Update `tool_content_planning` to receive or load active tools.
- Update planner prompt so it only selects available tools.
- Store selected tools, execution order, missing inputs, and missing capabilities.
- Add dry-run planner tests.

### Phase 4 - Dynamic execution plan

Goal: orchestrator begins executing selected tools from the stored plan.

Tasks:

- Add execution plan reader.
- Validate selected tools against registry before execution.
- Add tool run tracking.
- Add failure handling and retry policy.
- Keep compatibility with the existing fixed path during transition.

### Phase 5 - QA and repair loop

Goal: improve quality automatically.

Tasks:

- Add structured QA output schema.
- Add repair tool.
- Add repair attempt tracking.
- Add max repair attempt policy.
- Route unresolved issues to human review.

### Phase 6 - Client profile rules

Goal: make outputs client-aware.

Tasks:

- Expand client profile structure.
- Add brand voice, claims, forbidden claims, output defaults, approval defaults.
- Feed profile into analysis, planning, generation, and QA.

### Phase 7 - Asset module system

Goal: support reusable and pre-rendered assets.

Tasks:

- Define asset module schema.
- Add asset module registry/storage.
- Build asset pre-render workflow.
- Build product/module selector.
- Feed selected modules into planning and generation.

### Phase 8 - Specialist tools

Goal: replace generic generation with focused production tools.

Tasks:

- Split content generation into specialist tools.
- Add registry entries for each tool.
- Add tests and examples.
- Deprecate broad generic generation where specialist tools exist.

### Phase 9 - Delivery and packaging

Goal: make delivery client-ready.

Tasks:

- Improve delivery packs.
- Include outputs, assets, QA report, revision history, and metadata.
- Support client-specific delivery formats.

### Phase 10 - Production hardening

Goal: safe live operation.

Tasks:

- Live n8n execution tests.
- Credential checks.
- Postgres migration checks.
- Drive tests.
- LLM tests.
- Rollback procedure.
- Monitoring and alerting.
- Operator manual updates.

---

## 17. Near-term Build Priority

The next development target should be:

```text
v2.1 - Tool Registry and Planner Awareness
```

This is the foundation for all future modularity.

Do not start by building lots of new tools. First, make the planner aware of tools. Then make the orchestrator able to execute selected tools. Only then should the system grow more specialist tools.

Recommended v2.1 deliverables:

- `registry/tools.active.json`
- expanded `schemas/tool_registry.schema.json`
- all active workflows registered
- planner prompt updated with `available_tools`
- planner output includes `selected_tools` and `execution_order`
- missing capabilities captured
- validation checks added
- documentation for adding tools
- disabled example entry for `tool_asset_pre_renderer`

---

## 18. Definition of Done for Future Tools

A new tool is not complete until:

- n8n workflow exists in `workflows/active/` or is intentionally marked experimental/disabled
- tool registry entry exists
- input contract is documented
- output contract is documented
- credentials are listed
- database tables touched are listed
- dry-run mode is supported or explicitly marked unsupported
- failure mode is defined
- validation passes
- planner can see the tool
- planner can select the tool only when appropriate
- live execution has been tested before production use

---

## 19. Success Criteria

The system is moving in the right direction when:

1. A new tool can be added without rewriting the planner.
2. The planner selects tools from the active registry.
3. Missing capabilities are logged honestly.
4. Different job types produce different execution plans.
5. Client profile rules influence planning and QA.
6. Assets can be reused rather than regenerated every time.
7. QA can repair safe issues before human review.
8. Every job has a clear audit trail.
9. Deployment remains GitHub-controlled and repeatable.
10. n8n remains runtime only, not the source of truth.

---

## 20. Development Rules

1. Do not hardcode future capabilities into prompts without adding registry entries.
2. Do not let the planner invent tools.
3. Do not treat documentation-only registries as runtime truth.
4. Do not remove approval gates without replacing them with policy-driven controls.
5. Do not claim production readiness without live tests.
6. Do not build new specialist tools before the registry and planner awareness are in place.
7. Do not store secrets in the repository.
8. Do not edit live n8n workflows without exporting changes back to GitHub.
9. Keep the current pipeline working while introducing modular architecture.
10. Prefer non-breaking migrations until the new architecture is proven.

---

## 21. Final Direction

The AI Content n8n System should become a modular, tool-aware AI content production platform.

The heart of the platform is not one workflow. It is the relationship between:

```text
Tool Registry
+ Planning Engine
+ Execution Orchestrator
+ Asset/Client Context
+ QA and Repair
+ Delivery Pack
```

That is the system to build.

The immediate priority is to make the planning stage aware of available tools and force all future expansion through a proper registry. Once that foundation exists, the system can grow into a powerful, reusable content production engine instead of becoming a pile of clever but disconnected automations.
