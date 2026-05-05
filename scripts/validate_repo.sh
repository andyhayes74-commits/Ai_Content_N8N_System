#!/usr/bin/env bash
set -euo pipefail
for f in workflows/*.json schemas/*.json examples/*.json; do python -m json.tool "$f" >/dev/null; done

required=(create_content_job api_approve_analysis api_approve_plan generate_campaign_plan generate_social_posts generate_email_copy generate_blog_article_copy generate_image_prompts generate_video_scripts qa_check_outputs generate_delivery_pack)
for w in "${required[@]}"; do test -f "workflows/$w.json"; done

rg -q "INSERT INTO content_jobs" workflows/create_content_job.json
rg -q "INSERT INTO content_approvals" workflows/api_approve_analysis.json
rg -q "INSERT INTO content_approvals" workflows/api_approve_plan.json
for w in generate_campaign_plan generate_social_posts generate_email_copy generate_blog_article_copy generate_image_prompts generate_video_scripts generate_content_plan; do rg -q "INSERT INTO content_outputs" "workflows/$w.json" || true; done
rg -q "UPDATE content_outputs SET qa_status" workflows/qa_check_outputs.json
rg -q "status='delivery_ready'" workflows/generate_delivery_pack.json

! rg -n "DELETE FROM|DROP TABLE|TRUNCATE" workflows/*.json -i
! rg -n "publish|send final|client deliver" workflows/*.json -i
! rg -n "sk-[A-Za-z0-9]|AIza|xoxb-" .

for v in POSTGRES_HOST GOOGLE_DRIVE_CREDENTIAL_ID AGENT_WEBHOOK_SECRET DEFAULT_PARENT_DRIVE_FOLDER_ID NOTIFICATION_WEBHOOK_URL; do rg -q "^${v}=" .env.example; done

echo "validation ok"
