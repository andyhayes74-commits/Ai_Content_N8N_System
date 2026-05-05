# Workflow Orchestration Map

This system is modular. Each workflow should be imported into n8n separately, then called through webhooks or by supervisor/orchestration logic.

## Main sequence

```text
create_content_job
→ create_new_drive_project_folder OR register_existing_drive_folder
→ create_standard_folder_structure
→ scan_drive_assets
→ parse_and_summarise_documents
→ describe_images
→ handle_audio_video_references
→ create_asset_index
→ analyse_client_request
→ api_approve_analysis
→ generate_content_plan
→ api_approve_plan
→ route_output_tasks
→ generation workflows
→ qa_check_outputs
→ notify_user_for_review
→ api_approve_final_delivery
→ generate_delivery_pack
```

## Generation workflows

Run only after `api_approve_plan` has stored an approved `plan` decision:

```text
generate_campaign_plan
generate_social_posts
generate_email_copy
generate_blog_article_copy
generate_image_prompts
generate_video_scripts
```

## Approval gates

| Approval stage | Workflow | Unlocks |
|---|---|---|
| `analysis` | `api_approve_analysis` | `generate_content_plan` |
| `plan` | `api_approve_plan` | generation workflows |
| `final_delivery` | `api_approve_final_delivery` | `generate_delivery_pack` |

## Supervisor control workflows

```text
api_create_job
api_submit_message
api_attach_drive_folder
api_check_job_status
api_list_active_jobs
api_progress_updates
api_error_reports
api_request_revisions
api_retry_step
api_pause_job
api_resume_job
api_cancel_job
```

## Failure and recovery workflows

```text
log_errors
retry_safe_failed_steps
```

## Required headers

All webhook calls should include:

```text
x-agent-secret: <AGENT_WEBHOOK_SECRET>
```
