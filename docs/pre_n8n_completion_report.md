# Pre-n8n Completion Report

## Refactor completed

- Active workflows reduced from 40 debug workflows to 10 operator workflows.
- Old workflow JSON archived in `workflows/archive/v1_debug_build/`.
- Main orchestrator added at `workflows/active/ai_content_orchestrator.json`.
- Callable tool workflows added for intake, Drive assets, request analysis, planning, generation, QA/delivery, logging, supervisor API, and human review.
- Tool registry added in human-readable and machine-readable forms.
- Validation and import scripts now target `workflows/active/` only.

## Safety retained

- Analysis approval gate.
- Plan approval gate.
- Final human delivery approval gate.
- Agent safety boundaries.
- Postgres source of truth.
- Google Drive workspace layer.
- Dry-run test payloads.

## Schema note

Core tables are preserved. A non-breaking migration adds `content_approvals.reviewer_type` so workflows can explicitly distinguish human approvals from agent events.

## Not live-tested

No live n8n runtime execution was performed in this repository change. Postgres credentials, Google Drive OAuth, OpenAI/LiteLLM calls, supervisor callbacks, and notification delivery still require sandbox testing.


## Repair pass for PR #7 review blockers

- Hardened public webhook auth so n8n header-auth credentials guard the external entry points. Callable tool workflows are internal Execute Workflow targets.
- Removed unreachable business logic after early returns in active Code nodes.
- Made the orchestrator state-aware with action routing, selected tool lists, stage metadata, and accumulated `tool_results`.
- Repaired content-generation dispatch for `campaign_plan`, `social_posts`, `email_copy`, `blog_article`, `image_prompts`, and `video_scripts`.
- Added LLM response parsing before persistence for analysis, planning, generation, and QA/delivery tools, with parse warnings logged to `content_errors`.
- Strengthened validation to catch weak auth, unreachable code, missing LLM parsing, missing dispatch types, missing approval gates, and accidental archive/root imports.

No live n8n runtime or credentialed Postgres/Drive/LLM testing was performed during this repair pass.
