# v1.0 RC Audit (Post-Hardening Pass)

Audit date: 2026-05-05 (UTC).

## What changed in hardening pass
- Replaced non-executable placeholder workflow shells with connected n8n node chains in every `workflows/*.json` file.
- Added runtime secret checks (`x-agent-secret` vs `AGENT_WEBHOOK_SECRET`) for webhook-triggered workflows.
- Added explicit Postgres task/event/error writes per workflow.
- Added approval-gate SQL checks for analysis -> plan, plan -> output routing/generation, and final-delivery gate on delivery pack.
- Expanded `scripts/validate_repo.sh` to validate expected workflow files, webhook paths, SQL table references, approval checks, and forbidden destructive patterns.

## 1) Requirement Coverage Matrix
| Requirement | Implemented file(s) | Status | Notes |
|---|---|---|---|
| Modular workflow set exists | `workflows/*.json` | implemented | All required filenames present with connected nodes. |
| Durable Postgres state writes | `workflows/*.json`, `database/schema.sql` | partial | Task/event/error writes implemented; domain-specific output inserts remain limited template actions. |
| Approval gates runtime enforcement | `workflows/generate_content_plan.json`, `workflows/route_output_tasks.json`, `workflows/generate_*`, `workflows/generate_delivery_pack.json` | partial | SQL gate checks added; full business branching still template-grade. |
| Agent secret validation | `workflows/api_*.json` and all webhook flows | implemented | Header secret check added (`x-agent-secret`). |
| No destructive/publish/send behavior | `workflows/*.json`, `scripts/validate_repo.sh` | implemented | No delete/publish/send actions present; validation blocks forbidden patterns. |
| Fixture-driven dry run path | `examples/*.json`, `tests/sandbox_test_plan.md` | implemented | End-to-end dry-run order documented. |

## 2) n8n Workflow Readiness Matrix
All workflows are now valid import-ready JSON with connected nodes and executable SQL operations.

Common runtime dependencies:
- Credential: n8n Postgres credential (required now).
- Env vars: `AGENT_WEBHOOK_SECRET`, `POSTGRES_*`; others remain for future Google Drive/LLM integration.
- DB tables touched: `content_tasks`, `content_events`, `content_errors` (all); approval tables on gated workflows.

Logic maturity summary:
- **Executable template logic**: yes (webhook -> auth -> task/event -> gate -> response).
- **Business-complete production logic**: not yet (generation/output persistence still simplified template events for many workflows).

## 3) Safety Gate Verification
- Analysis approval gate: enforced in `generate_content_plan` (checks `content_approvals` stage `analysis`).
- Content plan approval gate: enforced in output routing/generation workflows (checks stage `plan`).
- Final delivery approval gate: enforced in `generate_delivery_pack` (checks stage `final_delivery`).
- Agent boundary: secret validation added; no schema edit, credential change, delete, publish, or final send operations implemented.
- No-delete/no-publish/no-send: enforced by workflow content + validation script forbidden-pattern checks.

## 4) Remaining Placeholder Inventory
- Domain-specific SQL payload handling remains generic template actions in many workflows.
- `content_outputs` writes are not yet comprehensively implemented for every generation workflow.
- Google Drive and LLM nodes are not wired because live credentials/services are unavailable in this environment.
- Agent role granularity beyond shared secret (e.g., per-action RBAC) is not implemented.

## 5) Dry-Run Execution Path
1. Configure `.env` from `.env.example`.
2. Apply `database/schema.sql` + `database/seed_reference.sql` to Postgres.
3. Import all `workflows/*.json` into n8n.
4. Call `v1/create_content_job` with `examples/client_brief.json` and `x-agent-secret` header.
5. Call asset and analysis flows in sequence using `examples/asset_index.json` and `examples/request_analysis.json`.
6. Add approval rows in `content_approvals` for `analysis`, then invoke `generate_content_plan`.
7. Add approval row for `plan`, then invoke `route_output_tasks` and output-generation workflows.
8. Invoke `qa_check_outputs` and `generate_delivery_pack` (requires `final_delivery` approval row).
9. Confirm task/event/error records in Postgres tables.

## 6) Remaining Live-Test Requirements
- Live n8n execution against real Postgres credential.
- Real Google Drive credential wiring and folder operations.
- Real LLM endpoint calls using prompts/schemas.
- Supervisor integration tests with OpenClaw/Hermes callbacks.

No live integration test was executed in this Codex environment.
