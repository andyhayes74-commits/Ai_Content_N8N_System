# Setup Guide
1. Copy `.env.example` to `.env` and fill placeholders.
2. Provision Postgres and run `database/schema.sql` then `database/seed_reference.sql`.
3. Import `workflows/*.json` into n8n.
4. Configure credential IDs in workflow nodes (Postgres, Google Drive, LLM provider, notification webhook).
5. Set webhook secret validation in API workflows.
6. Run dry-run fixtures from `examples/` and follow `tests/sandbox_test_plan.md`.

## Google Drive Folder Convention
`ClientName_ProjectName_Date/00_Admin..07_Delivery` must be created before writing outputs.
