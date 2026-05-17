# Smith Supervisor Agent - Design Brief

**Status:** Canonical design brief  
**System:** AI Content n8n System  
**Agent name:** Smith  
**Branch:** main  
**Purpose:** Define the supervisor agent that will oversee the AI Content n8n System without becoming a general-purpose agent platform.

---

## 1. Executive Summary

Smith is the dedicated supervisor agent for the AI Content n8n System.

Smith is not the production workflow engine, not a replacement for n8n, not a general personal assistant, and not an OpenClaw-style autonomous platform. Smith is a controlled operational intelligence layer that watches jobs, understands the tool registry, reviews workflow state, answers operator questions, detects problems, recommends safe actions, and eventually performs limited low-risk actions within strict policy.

The core architecture is:

```text
Telegram / operator interface
→ Smith supervisor service
→ Postgres operational state
→ tool registry
→ n8n API/webhooks
→ optional LLM reasoning calls
```

Smith should be built as a standalone Dockerised service, probably using Python FastAPI or Node/TypeScript, with Postgres as its memory and source of operational truth.

Smith must not rely on long-running OpenAI chat history for workflow decisions. Automated workflow reasoning must use fresh, isolated sessions with curated context packets. Human interactions must use persistent but bounded conversation threads so Smith can answer natural follow-up questions such as “why did it fail?”, “how long left?”, or “give me a progress update”.

---

## 2. Why Smith Exists

The AI Content n8n System is designed to become a modular content production platform. As the system grows, it will include many jobs, tools, assets, client profiles, approvals, errors, retries, QA checks, and delivery stages.

Without a supervisor layer, the operator has to inspect n8n, Postgres, logs, GitHub, and Telegram manually. Smith exists to reduce that operational burden.

Smith should answer questions like:

- What jobs are running?
- What jobs are stuck?
- What needs approval?
- Why did this workflow fail?
- Which tool failed?
- Is this safe to retry?
- How long is this process likely to take?
- Which capabilities are missing from the system?
- Did the planner select valid tools?
- Which tool should be built next?
- Are there repeated failures that indicate a system problem?

Smith turns the platform from a set of workflows into something that feels watched, managed, and understandable.

---

## 3. What Smith Is

Smith is:

1. **A supervisor agent.**
   Smith observes, explains, recommends, and later performs limited safe actions.

2. **A domain-specific operational agent.**
   Smith is built specifically for the AI Content n8n System.

3. **A Postgres-aware service.**
   Smith reads job state, events, errors, outputs, approvals, tool plans, and tool runs from Postgres.

4. **A tool-registry-aware service.**
   Smith understands what tools exist, what they do, what inputs they need, and whether they are active, disabled, experimental, or deprecated.

5. **An n8n-aware service.**
   Smith can inspect workflow state and eventually call safe n8n actions through approved APIs or webhooks.

6. **A Telegram-capable service.**
   Smith can communicate directly through Telegram without needing OpenClaw.

7. **An audit-first service.**
   Smith records sessions, recommendations, actions, explanations, and operator interactions.

8. **A safety-bounded agent.**
   Smith has explicit permission levels and must not bypass approval policy.

---

## 4. What Smith Is Not

Smith is not:

1. **A replacement for n8n.**
   n8n remains the workflow runtime.

2. **A replacement for the planner.**
   The planner creates execution plans. Smith reviews, explains, and monitors them.

3. **A general agent platform.**
   Smith is not intended to become a broad OpenClaw-style personal assistant system.

4. **A workflow itself.**
   Smith should not be implemented as only another n8n workflow. It should be its own service.

5. **A long-running OpenAI chat thread.**
   Smith must not send old workflow/session history into every model call.

6. **An approval bypass.**
   Smith must not impersonate a human reviewer where human approval is required.

7. **A secret holder in GitHub.**
   Tokens, API keys, and credentials must stay outside the repository.

---

## 5. Recommended Platform

Smith should be built as a custom Dockerised service.

Recommended stack:

```text
Service: ai-content-smith
Language: Python FastAPI preferred, Node/TypeScript acceptable
Database: existing Postgres
Workflow control: n8n API/webhooks
Messaging: direct Telegram bot adapter
LLM: OpenAI/OpenRouter/LiteLLM as optional reasoning layer
Deployment: Docker Compose alongside n8n/Postgres
```

### 5.1 Why custom service instead of OpenClaw

Smith needs strict control, predictable state handling, and narrow permissions. It will eventually touch operational data, job status, approval information, and workflow control actions. A general-purpose agent framework would add unnecessary complexity and permission risk.

OpenClaw or similar systems may still be used later as a communication bridge, but they should not be Smith’s core brain.

### 5.2 Direct Telegram integration

Smith should communicate directly with Telegram using a bot token created through BotFather.

Initial mode:

```text
Long polling
```

Production mode:

```text
HTTPS webhook
```

Direct Telegram keeps the communication layer simple and avoids relying on OpenClaw.

---

## 6. High-Level Architecture

```text
Telegram / operator
        ↓
Smith Telegram Adapter
        ↓
Smith API / command router
        ↓
Context resolver
        ↓
Supervisor core
        ↓
Postgres + Tool Registry + n8n API
        ↓
Optional LLM reasoning
        ↓
Recommendation / response / action log
```

### 6.1 Component overview

| Component | Purpose |
|---|---|
| Telegram Adapter | Receives and sends Telegram messages. |
| Command Router | Maps commands and natural-language requests to Smith intents. |
| Context Resolver | Determines which job, workflow, tool, error, or approval the user means. |
| Supervisor Core | Runs deterministic checks and coordinates Smith logic. |
| Job Monitor | Finds active, stuck, failed, or waiting jobs. |
| Tool Registry Reader | Loads and validates available tools. |
| n8n Connector | Reads or triggers approved n8n actions. |
| Postgres Connector | Reads and writes operational state. |
| LLM Reasoning Layer | Produces explanations, diagnoses, and recommendations from curated context. |
| Action Policy Engine | Decides whether Smith may perform, suggest, or block an action. |
| Audit Logger | Records sessions, actions, recommendations, and human interactions. |

---

## 7. Smith Permission Levels

Smith must be permission-tiered. Do not start with broad action permissions.

### Level 0 - Read-only Observer

Smith can:

- read job state
- read recent events
- read recent errors
- read pending approvals
- read tool registry
- answer status questions
- produce summaries

Smith cannot:

- retry jobs
- pause jobs
- approve anything
- trigger workflows
- modify data

### Level 1 - Operator Assistant

Smith can:

- recommend retries
- recommend approvals
- explain failures
- identify missing inputs
- identify missing capabilities
- prepare suggested actions

Smith cannot execute actions without confirmation.

### Level 2 - Safe Automation Agent

Smith can automatically perform low-risk actions, such as:

- retry explicitly retryable failures
- run safe repair steps
- pause obviously stuck jobs
- send notifications
- request missing input

All actions must be logged.

### Level 3 - Production Supervisor

Smith can manage jobs within defined policy:

- trigger next stages
- route safe repair actions
- escalate high-risk issues
- manage approval requests
- monitor tool health

### Level 4 - Development Assistant

Smith can help improve the platform:

- identify repeated missing capabilities
- suggest new tools
- open GitHub issues if explicitly enabled
- draft Codex prompts
- report workflow design problems

Smith must not directly edit live n8n workflows or merge GitHub changes without explicit human approval.

---

## 8. Session Model

Smith needs two separate session types.

```text
1. Workflow Event Sessions
2. Human Conversation Threads
```

This is a core design requirement.

---

## 9. Workflow Event Sessions

Workflow event sessions are fresh, isolated, and scoped to one operational event.

Examples:

- workflow started
- workflow failed
- QA failed
- approval needed
- delivery ready
- missing capability detected
- tool timeout
- retry decision needed

### 9.1 Workflow session rule

Smith must create a fresh session for every workflow event.

Smith must not send previous Smith workflow sessions, old Telegram chat history, or unrelated job history to the LLM by default.

### 9.2 Workflow session lifecycle

```text
Workflow event occurs
→ create Smith workflow session
→ fetch relevant job/tool/error/context state
→ build curated context packet
→ run deterministic checks
→ optionally ask LLM for diagnosis/recommendation
→ store recommendation
→ notify operator if needed
→ close session
```

### 9.3 Workflow session context packet

Example:

```json
{
  "smith_session_id": "smith_2026_05_14_001",
  "session_type": "workflow_failed",
  "task": "Diagnose workflow failure and recommend next action",
  "job": {
    "job_id": "job_123",
    "status": "qa_failed",
    "requested_outputs": ["social_posts", "image_prompts"]
  },
  "workflow": {
    "workflow_name": "tool_qa_delivery",
    "run_id": "run_789",
    "failed_node": "Parse QA JSON",
    "error_type": "invalid_json"
  },
  "relevant_events": [
    "content generation completed",
    "QA model returned invalid JSON",
    "repair attempt count: 0"
  ],
  "tool_registry_entry": {},
  "available_actions": [
    "retry_tool",
    "run_repair",
    "request_human_review",
    "mark_failed"
  ],
  "rules": {
    "do_not_approve_delivery": true,
    "max_repair_attempts": 2,
    "only_recommend_registered_actions": true
  }
}
```

### 9.4 Workflow session output

Smith should produce structured recommendations:

```json
{
  "recommended_action": "run_repair",
  "requires_human": false,
  "confidence": 0.82,
  "reasoning_summary": "The failure is a recoverable JSON parse error and no repair attempt has been made yet.",
  "risk_level": "low"
}
```

Store reasoning summaries, not large hidden reasoning traces.

---

## 10. Human Conversation Threads

Human conversation threads are persistent but bounded. They allow Smith to answer natural follow-up questions without carrying the entire conversation into every LLM call.

Examples:

```text
Andy: Progress update?
Andy: Why did it fail?
Andy: How long left?
Andy: Retry it.
Andy: What tool is missing?
```

### 10.1 Human thread rule

Smith must preserve enough human context to resolve references like:

- it
- that job
- the failed one
- the current process
- the image workflow
- the approval waiting now

Smith must not send raw long-running Telegram history into OpenAI by default.

### 10.2 Human thread fields

Smith should track:

```text
thread_id
channel
telegram_user_id
status
current_job_id
current_workflow_run_id
current_topic
last_referenced_job_id
last_referenced_error_id
last_referenced_tool_id
last_action_suggested
created_at
updated_at
```

### 10.3 Human message fields

Smith should store:

```text
message_id
thread_id
sender
message_text
intent
linked_job_id
linked_tool_id
created_at
```

### 10.4 Human context summary

Smith should maintain compact summaries, for example:

```text
Andy is currently discussing job_123. The last question was about why tool_qa_delivery failed. Smith recommended one repair attempt before human review.
```

This summary may be included in future LLM calls. Raw history should not be included unless explicitly needed.

### 10.5 Human question answering flow

```text
Human message arrives
→ authenticate user
→ identify intent
→ resolve context
→ fetch relevant state
→ build small context packet
→ answer deterministically where possible
→ optionally use LLM to explain clearly
→ store response
→ update human thread context
```

---

## 11. Context Resolver

The context resolver is one of Smith’s most important parts.

It maps vague human questions to operational state.

Examples:

| User says | Smith resolves |
|---|---|
| “Progress update?” | current_job_id from active thread, or active jobs summary if none. |
| “Why did it fail?” | latest failed job/tool in thread context. |
| “How long left?” | current job’s selected tools, completed stages, historical runtimes. |
| “Retry it.” | last failed job/action, then requires confirmation unless low-risk policy allows. |
| “What tools are missing?” | missing capabilities from recent planner outputs. |

If Smith cannot resolve the context safely, it must ask a clarifying question rather than guessing.

---

## 12. Telegram Interface

### 12.1 Direct Telegram bot

Smith should use a direct Telegram bot adapter. OpenClaw is not required.

### 12.2 Access control

Smith must only respond to approved Telegram user IDs.

Minimum security rules:

```text
- allowlist Telegram user IDs
- reject unknown users
- never send secrets
- log all commands
- require confirmation for risky actions
- never bypass approval policy
```

### 12.3 Suggested commands

Initial read-only commands:

```text
/status
/jobs
/stuck
/approvals
/errors
/tools
/missing
/job <job_id>
/help
```

Later action commands:

```text
/retry <job_id>
/pause <job_id>
/resume <job_id>
/request_review <job_id>
/approve_plan <job_id>
/approve_delivery <job_id>
```

Approval commands should require confirmation.

Example:

```text
Smith: Approve final delivery for job_123? Reply CONFIRM APPROVE job_123.
```

---

## 13. Smith Capabilities

### 13.1 v0.1 capabilities

Smith v0.1 should be read-only.

It should support:

- direct Telegram bot integration
- allowed-user security
- active jobs summary
- stuck jobs summary
- pending approvals summary
- recent errors summary
- active tool registry summary
- missing capabilities summary
- job detail view
- human thread tracking
- workflow session creation
- context packet logging

### 13.2 v0.2 capabilities

Smith v0.2 may add:

- recommendations
- failure explanation
- estimated time remaining
- tool health summary
- daily status summary
- operator notifications

### 13.3 v0.3 capabilities

Smith v0.3 may add safe actions:

- retry low-risk failures
- run repair workflow
- pause stuck jobs
- request human review
- create incident records

### 13.4 v1.0 capabilities

Smith v1.0 should be a production supervisor:

- policy-controlled actions
- complete audit trail
- stable Telegram interface
- tool health scoring
- missing capability intelligence
- approval workflow integration
- robust failure handling
- deployment/health checks

---

## 14. Time Estimation

Smith should estimate runtime using data, not guesswork.

Inputs:

- selected tools from the tool execution plan
- `average_runtime` from tool registry
- actual historical tool run durations
- completed stages
- failed/retry state
- queue/concurrency state

Initial estimate format:

```text
Estimated remaining time: 3 to 6 minutes.
```

Smith should explain what the estimate is based on.

Example:

```text
Generation is the slowest remaining step. The estimate is based on the selected tools and previous successful runs.
```

If no useful data exists, Smith should say so.

---

## 15. Failure Diagnosis

Smith should classify failures into clear categories:

- credential error
- missing input
- invalid model output
- invalid JSON
- QA failure
- approval missing
- n8n execution error
- Postgres error
- Drive error
- timeout
- tool unavailable
- unknown

Smith should recommend actions from an approved list only:

- retry tool
- run repair
- request missing input
- request human review
- pause job
- mark failed
- create incident
- escalate to operator

Smith must not invent actions.

---

## 16. Tool Registry Awareness

Smith must read the active tool registry.

Smith should know:

- which tools exist
- which tools are active
- which tools are disabled
- which tools are experimental
- which tools are deprecated
- what each tool does
- what inputs each tool requires
- what outputs each tool creates
- what credentials each tool needs
- what failure mode each tool has

Smith should use this to:

- explain plans
- detect invalid selected tools
- detect missing capabilities
- estimate runtime
- diagnose tool failures
- suggest future tool development

---

## 17. Data Model Direction

Smith should add or use the following tables.

### 17.1 `smith_sessions`

```text
id
session_type
job_id
workflow_run_id
trigger_event
status
created_at
closed_at
```

### 17.2 `smith_context_packets`

```text
id
smith_session_id
context_json
token_estimate
created_at
```

### 17.3 `smith_recommendations`

```text
id
smith_session_id
recommendation_type
recommended_action
confidence
requires_human
risk_level
reasoning_summary
created_at
```

### 17.4 `smith_actions`

```text
id
smith_session_id
action_type
job_id
requested_by
approved_by
status
result_json
created_at
completed_at
```

### 17.5 `smith_human_threads`

```text
id
channel
external_user_id
status
current_job_id
current_workflow_run_id
current_topic
last_referenced_job_id
last_referenced_error_id
last_referenced_tool_id
last_action_suggested
created_at
updated_at
```

### 17.6 `smith_human_messages`

```text
id
thread_id
sender
message_text
intent
linked_job_id
linked_tool_id
created_at
```

### 17.7 `smith_human_summaries`

```text
id
thread_id
summary_text
covered_message_count
created_at
```

---

## 18. LLM Usage Rules

Smith should use LLM calls carefully.

### 18.1 Do use LLM for

- explaining failures clearly
- summarising complex job state
- recommending next action from allowed actions
- identifying likely root causes from curated context
- writing operator-friendly messages
- interpreting ambiguous human questions after deterministic context resolution

### 18.2 Do not use LLM for

- basic database queries
- access control
- permission decisions
- approval enforcement
- secret handling
- selecting unauthorized actions
- reading raw long-term history by default

### 18.3 Prompting rule

Every LLM call should include:

- fresh system instruction
- bounded context packet
- clear task
- allowed actions
- output schema

It should not include:

- full previous sessions
- full Telegram chat history
- unrelated jobs
- raw secrets
- unnecessary logs

---

## 19. Security Rules

Smith must follow these rules:

1. Store Telegram bot token outside GitHub.
2. Store API keys outside GitHub.
3. Use Telegram user allowlist.
4. Log all commands and actions.
5. Require confirmation for risky actions.
6. Do not send secrets over Telegram.
7. Do not expose raw credentials in logs.
8. Do not approve final delivery unless policy allows Smith approval.
9. Do not execute disabled or deprecated tools.
10. Do not run experimental tools unless explicitly enabled.
11. Do not use LLM output as permission authority.
12. Keep dangerous actions behind deterministic policy checks.

---

## 20. API Endpoints

Smith may expose internal endpoints such as:

```text
GET /health
GET /status
GET /jobs/active
GET /jobs/stuck
GET /jobs/{job_id}
GET /approvals/pending
GET /errors/recent
GET /tools
GET /missing-capabilities
POST /telegram/webhook
POST /sessions/workflow-event
POST /actions/retry
POST /actions/pause
POST /actions/resume
POST /actions/request-review
```

Action endpoints must require authentication and policy checks.

---

## 21. Deployment Model

Smith should run as a Docker container alongside the main system.

Example service name:

```text
ai-content-smith
```

Required environment variables:

```text
SMITH_ENV=development|production
DATABASE_URL=postgres://...
N8N_BASE_URL=https://...
N8N_API_KEY=...
TELEGRAM_BOT_TOKEN=...
TELEGRAM_ALLOWED_USER_IDS=...
LLM_PROVIDER=openai|openrouter|litellm|none
LLM_API_KEY=...
SMITH_PERMISSION_LEVEL=0
```

Secrets must be provided through environment variables or secret management, not committed files.

---

## 22. Development Roadmap

### Phase 1 - Design and scaffolding

- Add this design brief.
- Create Smith service folder.
- Add Dockerfile and Compose example.
- Add config loader.
- Add health endpoint.
- Add Postgres connection.

### Phase 2 - Read-only monitor

- Read active jobs.
- Read stuck jobs.
- Read pending approvals.
- Read recent errors.
- Read active tool registry.
- Return system status summary.

### Phase 3 - Telegram read-only interface

- Add Telegram bot adapter.
- Add allowed-user check.
- Add `/status`, `/jobs`, `/stuck`, `/approvals`, `/errors`, `/tools`, `/missing`, `/job` commands.
- Add human thread tracking.

### Phase 4 - Workflow event sessions

- Add `smith_sessions`.
- Add context packet builder.
- Add workflow event endpoint.
- Store recommendations.
- Close sessions after each event.

### Phase 5 - Human conversation threads

- Add human thread context resolver.
- Support follow-up questions.
- Maintain compact thread summaries.
- Avoid raw long-history prompts.

### Phase 6 - LLM reasoning layer

- Add bounded model calls.
- Add strict output schemas.
- Add failure diagnosis.
- Add action recommendation.
- Add operator-friendly explanations.

### Phase 7 - Safe actions

- Add retry recommendations.
- Add confirmed retry action.
- Add pause/resume actions.
- Add repair action hook.
- Add action audit log.

### Phase 8 - Production supervisor

- Add tool health scoring.
- Add missing capability reports.
- Add daily summaries.
- Add approval request flow.
- Add production deployment checks.

---

## 23. Smith v0.1 Definition of Done

Smith v0.1 is complete when:

- Smith runs as its own service.
- Smith connects to Postgres.
- Smith reads active jobs.
- Smith reads pending approvals.
- Smith reads recent errors.
- Smith reads the tool registry.
- Smith exposes a health endpoint.
- Smith has a direct Telegram bot adapter.
- Telegram access is limited to allowed users.
- `/status` works.
- `/jobs` works.
- `/stuck` works.
- `/approvals` works.
- `/errors` works.
- `/tools` works.
- Smith stores human thread context.
- Smith does not perform write actions.
- Smith does not use long-running OpenAI chat history.

---

## 24. Final Direction

Smith should become the calm operational supervisor for the AI Content n8n System.

Smith should not be magical, vague, or overpowered. It should be controlled, auditable, useful, and narrow.

The long-term relationship should be:

```text
n8n does the work.
Postgres stores the truth.
The tool registry defines capabilities.
The planner chooses tools.
Smith watches, explains, recommends, and safely supervises.
Andy stays in control.
```

The immediate priority is to build Smith as a read-only Telegram-capable supervisor with clean session isolation and bounded human conversation context. Once that foundation is stable, Smith can grow into safe actions, approvals, repair triggers, and production supervision.
