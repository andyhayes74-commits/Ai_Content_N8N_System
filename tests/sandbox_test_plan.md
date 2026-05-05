# Sandbox Test Plan
1. Apply schema to local Postgres.
2. Import workflows into n8n sandbox instance.
3. Run `create_content_job` with `examples/client_brief.json`.
4. Replay asset parsing using `examples/asset_index.json`.
5. Inject analysis and plan fixtures to approval flows.
6. Validate QA and delivery pack generation fixtures.
7. Validate API status and error response fixtures.

Limitations: No live Google Drive/LLM execution in this repository-only test pass.
