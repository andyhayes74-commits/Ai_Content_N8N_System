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
