#!/usr/bin/env bash
set -euo pipefail

required_workflows=(
create_content_job register_existing_drive_folder create_new_drive_project_folder create_standard_folder_structure
scan_drive_assets parse_and_summarise_documents describe_images handle_audio_video_references create_asset_index
analyse_client_request generate_content_plan wait_for_human_approval route_output_tasks generate_campaign_plan
generate_social_posts generate_email_copy generate_blog_article_copy generate_image_prompts generate_video_scripts
qa_check_outputs generate_delivery_pack notify_user_for_review log_progress_events log_errors retry_safe_failed_steps
api_create_job api_submit_message api_attach_drive_folder api_check_job_status api_list_active_jobs api_progress_updates
api_error_reports api_approve_analysis api_approve_plan api_request_revisions api_retry_step api_pause_job api_resume_job api_cancel_job
)

for wf in "${required_workflows[@]}"; do
  test -f "workflows/${wf}.json"
  python -m json.tool "workflows/${wf}.json" >/dev/null
  rg -q '"path": "v1/' "workflows/${wf}.json"
  rg -q 'content_tasks|content_events|content_errors' "workflows/${wf}.json"
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

# approval gate enforcement checks in relevant workflows
rg -q "approval_stage='analysis'" workflows/generate_content_plan.json
rg -q "approval_stage='plan'" workflows/route_output_tasks.json
rg -q "approval_stage='final_delivery'" workflows/generate_delivery_pack.json

# destructive action guard
if rg -n "delete from|drop table|publish|send final" workflows/*.json -i; then
  echo "Forbidden destructive/publish pattern found" >&2
  exit 1
fi

echo "workflow hardening checks ok"
