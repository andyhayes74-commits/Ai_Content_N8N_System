# Build Plan: AI Content n8n System v1.0 RC

## Objectives
Build a production-oriented, modular n8n automation repository for freelance AI content operations with durable state in Postgres, file workspace in Google Drive, and supervisor orchestration through webhook/API workflows.

## Assumptions
1. n8n instance is self-hosted and can use Postgres, Google Drive, and HTTP Request nodes.
2. Audio/video deep transcription is deferred to adapter placeholders until user wires third-party services.
3. AI model access is available via OpenAI API or LiteLLM-compatible endpoint.
4. Human approvals happen externally (supervisor UI/chat) and are submitted back via API workflows.

## Phases
1. Repository scaffold and naming conventions.
2. Database schema + constraints + seed enums.
3. JSON schemas for AI structured outputs.
4. Prompt library for analysis, planning, generation, QA, and delivery.
5. Modular n8n workflow JSON templates.
6. Agent supervisor API workflow set.
7. Examples/fixtures for dry runs.
8. Setup, testing, failure recovery, and release documentation.
9. Validation pass for JSON and SQL consistency.

## Non-Goals for RC
- Live credentialed integration tests.
- Autonomous publishing/posting or client sending.
- File deletion and irreversible actions.
