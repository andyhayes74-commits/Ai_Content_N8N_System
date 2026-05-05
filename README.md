# AI Content n8n System (v1.0 Release Candidate)

Production-oriented modular automation framework for freelance AI content operations.

## Architecture
- **n8n**: execution/orchestration layer using modular workflows.
- **Postgres**: durable state and source of truth.
- **Google Drive**: per-job workspace and output storage.
- **AI supervisor (OpenClaw/Hermes)**: sends commands and receives progress via webhook-style API workflows.
- **LLM providers**: request analysis, planning, copy generation, QA.

## Repository Layout
- `workflows/` modular n8n workflow JSON files.
- `prompts/` AI instruction templates.
- `schemas/` strict JSON schemas for structured AI outputs.
- `database/` schema and reference seed data.
- `examples/` sandbox fixtures.
- `tests/` dry-run test plan.
- `docs/` setup, API, recovery, and release docs.
- `scripts/` validation helpers.

## Required Human Approval Gates
1. After request analysis.
2. After content plan generation.
3. Before final delivery.

## Supported Outputs
Campaign plans, social posts, email copy, blog/article copy, image prompts, video scripts, shot lists/storyboard/edit notes, and delivery summaries.

## Job Status Values
`created`, `intake_complete`, `assets_scanning`, `assets_parsed`, `analysis_complete`,
`waiting_for_analysis_approval`, `waiting_for_plan_approval`, `generating_outputs`,
`qa_in_progress`, `waiting_for_human_review`, `delivery_ready`, `completed`, `failed`, `paused`, `cancelled`.

## Google Drive Folder Standard
`ClientName_ProjectName_Date/`
- `00_Admin/`
- `01_Input/`
- `02_Parsed/`
- `03_Strategy/`
- `04_Copy/`
- `05_Images/`
- `06_Video/`
- `07_Delivery/`

## Quick Start
1. Read `docs/setup_guide.md`.
2. Configure `.env` from `.env.example`.
3. Apply SQL in `database/schema.sql`.
4. Import workflows from `workflows/`.
5. Run `scripts/validate_repo.sh`.
6. Execute dry-run fixtures via `tests/sandbox_test_plan.md`.

## Safety Constraints
- No file delete operations.
- No autonomous publishing or final client sending.
- No credential/schema modification via agent endpoints.
- No final delivery approval without explicit human approval.

## Testing Scope in this RC
Includes static validation and sandbox fixtures only; live credential integrations are intentionally marked as pending user environment configuration.
