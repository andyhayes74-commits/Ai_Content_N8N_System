# Sandbox Test Plan

This plan is for the first n8n sandbox run after the repo passes GitHub preflight.

## Header required for every webhook call

```text
x-agent-secret: <AGENT_WEBHOOK_SECRET>
```

## Payload sequence

Use files in `tests/payloads/` in this order:

1. `01_create_content_job.json` → `create_content_job`
2. Copy returned `job_id` into all later payloads.
3. `02_register_existing_drive_folder.json` → `register_existing_drive_folder`
4. `03_create_standard_folder_structure.json` → `create_standard_folder_structure`
5. `04_scan_drive_assets.json` → `scan_drive_assets`
6. `05_create_asset_index.json` → `create_asset_index`
7. `06_analyse_client_request_dry_run.json` → `analyse_client_request`
8. `07_approve_analysis.json` → `api_approve_analysis`
9. `08_generate_content_plan_dry_run.json` → `generate_content_plan`
10. `09_approve_plan.json` → `api_approve_plan`
11. `10_route_output_tasks.json` → `route_output_tasks`
12. `11_generate_campaign_plan_dry_run.json` → `generate_campaign_plan`
13. `12_generate_social_posts_dry_run.json` → `generate_social_posts`
14. `13_generate_email_copy_dry_run.json` → `generate_email_copy`
15. `14_generate_blog_article_copy_dry_run.json` → `generate_blog_article_copy`
16. `15_generate_image_prompts_dry_run.json` → `generate_image_prompts`
17. `16_generate_video_scripts_dry_run.json` → `generate_video_scripts`
18. `17_qa_check_outputs_dry_run.json` → `qa_check_outputs`
19. `18_approve_final_delivery.json` → `api_approve_final_delivery`
20. `19_generate_delivery_pack.json` → `generate_delivery_pack`

## Database checks

Run `tests/expected_db_checks.sql` after replacing `:job_id` with the job UUID.

## Expected final state

- `content_jobs.status = delivery_ready`
- `content_outputs` contains request analysis, asset index, content plan, generation outputs, QA report, and delivery pack
- `content_approvals` contains approved `analysis`, `plan`, and `final_delivery` rows
- no unresolved critical errors

## Live-mode testing

After dry-run path passes, repeat selected LLM workflows without `mode: dry_run` to test OpenAI/LiteLLM calls.

Then test Drive workflows using a real test Google Drive parent folder.
