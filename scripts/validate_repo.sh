#!/usr/bin/env bash
set -euo pipefail

required_workflows=(
create_content_job register_existing_drive_folder create_new_drive_project_folder create_standard_folder_structure
scan_drive_assets parse_and_summarise_documents describe_images handle_audio_video_references create_asset_index
analyse_client_request generate_content_plan wait_for_human_approval route_output_tasks generate_campaign_plan
generate_social_posts generate_email_copy generate_blog_article_copy generate_image_prompts generate_video_scripts
qa_check_outputs generate_delivery_pack notify_user_for_review log_progress_events log_errors retry_safe_failed_steps
api_create_job api_submit_message api_attach_drive_folder api_check_job_status api_list_active_jobs api_progress_updates
api_error_reports api_approve_analysis api_approve_plan api_approve_final_delivery api_request_revisions api_retry_step api_pause_job api_resume_job api_cancel_job
)

for wf in "${required_workflows[@]}"; do
  test -f "workflows/${wf}.json"
  python -m json.tool "workflows/${wf}.json" >/dev/null
  rg -q '"path":"v1/|"path": "v1/' "workflows/${wf}.json"
  rg -q 'x-agent-secret|X-Agent-Secret' "workflows/${wf}.json"
done

for f in schemas/*.json examples/*.json; do python -m json.tool "$f" >/dev/null; done

python - <<'PY'
import pathlib
sql=pathlib.Path('database/schema.sql').read_text()
required=['content_jobs','content_assets','content_outputs','content_tasks','content_events','content_errors','content_approvals','client_profiles','job_messages']
missing=[t for t in required if t not in sql]
assert not missing, missing
print('schema check ok')
PY

if rg -n '\|\|\s*}}|\{\$json|\$json\.body\.job_id\s*\|\||template action|NULLIF\('\''\{\$json' workflows scripts docs -S; then
  echo "Malformed expression or template-only action found" >&2
  exit 1
fi

rg -q "INSERT INTO content_jobs" workflows/create_content_job.json
rg -q "INSERT INTO content_jobs" workflows/api_create_job.json
rg -q "INSERT INTO content_approvals" workflows/api_approve_analysis.json
rg -q "INSERT INTO content_approvals" workflows/api_approve_plan.json
rg -q "final_delivery" workflows/api_approve_final_delivery.json
rg -q "reviewer_type" workflows/api_approve_final_delivery.json
rg -q "INSERT INTO content_outputs" workflows/create_asset_index.json
rg -q "INSERT INTO content_outputs" workflows/analyse_client_request.json
rg -q "INSERT INTO content_outputs" workflows/generate_content_plan.json
for wf in generate_campaign_plan generate_social_posts generate_email_copy generate_blog_article_copy generate_image_prompts generate_video_scripts; do
  rg -q "INSERT INTO content_outputs" "workflows/${wf}.json"
  rg -q "approval_stage='plan'" "workflows/${wf}.json"
done
rg -q "UPDATE content_outputs" workflows/qa_check_outputs.json
rg -q "output_type','qa_report'" workflows/qa_check_outputs.json
rg -q "output_type','delivery_pack'" workflows/generate_delivery_pack.json
rg -q "delivery_ready" workflows/generate_delivery_pack.json
rg -q "INSERT INTO job_messages" workflows/api_submit_message.json
rg -q "INSERT INTO content_errors" workflows/log_errors.json
rg -q "retry_count < max_retries" workflows/retry_safe_failed_steps.json

if rg -n "DELETE FROM|DROP TABLE|TRUNCATE|publish|send final|client deliver" workflows/*.json -i; then
  echo "Forbidden destructive/publish/send pattern found" >&2
  exit 1
fi
if rg -n "sk-[A-Za-z0-9]|AIza|xox[baprs]-" .; then
  echo "Potential hardcoded secret found" >&2
  exit 1
fi

for v in POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD GOOGLE_DRIVE_CREDENTIAL_ID DEFAULT_PARENT_DRIVE_FOLDER_ID AGENT_WEBHOOK_SECRET NOTIFICATION_WEBHOOK_URL; do
  rg -q "^${v}=" .env.example
done

echo "validation ok"
