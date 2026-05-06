#!/usr/bin/env bash
set -euo pipefail

python scripts/build_llm_workflows.py >/dev/null
python scripts/embed_llm_prompts.py >/dev/null
python scripts/build_drive_workflows.py >/dev/null
python scripts/fix_generated_n8n_expressions.py >/dev/null
bash scripts/check_workflow_drift.sh >/dev/null

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

python - <<'PY'
import re, sys
from pathlib import Path
bad = re.compile(r"\|\|\s*}}|(?<!\{)\{\$json|(?<!\{)\{\$env|(?<!\{)\{\$node|\$json\.body\.job_id\s*\|\||template action|NULLIF\('(?<!\{)\{\$json")
fail=[]
for p in Path('workflows').glob('*.json'):
    text=p.read_text(errors='ignore')
    if bad.search(text): fail.append(str(p))
if fail:
    print('Malformed expression or template-only action found:')
    print('\n'.join(fail))
    sys.exit(1)
PY

python - <<'PY'
from pathlib import Path
checks = [
    ('workflows/create_content_job.json', 'INSERT INTO content_jobs'),
    ('workflows/api_create_job.json', 'INSERT INTO content_jobs'),
    ('workflows/api_approve_analysis.json', 'INSERT INTO content_approvals'),
    ('workflows/api_approve_plan.json', 'INSERT INTO content_approvals'),
    ('workflows/api_approve_final_delivery.json', 'final_delivery'),
    ('workflows/api_approve_final_delivery.json', 'reviewer_type'),
    ('workflows/create_asset_index.json', 'INSERT INTO content_outputs'),
    ('workflows/analyse_client_request.json', 'INSERT INTO content_outputs'),
    ('workflows/generate_content_plan.json', 'INSERT INTO content_outputs'),
    ('workflows/qa_check_outputs.json', 'UPDATE content_outputs'),
    ('workflows/qa_check_outputs.json', 'qa_report'),
    ('workflows/generate_delivery_pack.json', 'delivery_pack'),
    ('workflows/generate_delivery_pack.json', 'delivery_ready'),
    ('workflows/api_submit_message.json', 'INSERT INTO job_messages'),
    ('workflows/log_errors.json', 'INSERT INTO content_errors'),
    ('workflows/retry_safe_failed_steps.json', 'retry_count < max_retries'),
    ('workflows/describe_images.json', 'description_sql'),
    ('workflows/log_progress_events.json', 'message_sql'),
]
for wf in ['generate_campaign_plan','generate_social_posts','generate_email_copy','generate_blog_article_copy','generate_image_prompts','generate_video_scripts']:
    checks.append((f'workflows/{wf}.json','INSERT INTO content_outputs'))
    checks.append((f'workflows/{wf}.json',"approval_stage='plan'"))
missing=[]
for file, needle in checks:
    text=Path(file).read_text(errors='ignore')
    if needle not in text:
        missing.append(f'{file}: missing marker {needle!r}')
if missing:
    print('Validation marker checks failed:')
    print('\n'.join(missing))
    raise SystemExit(1)
print('marker checks ok')
PY

python - <<'PY'
from pathlib import Path
bad=[]
for wf in ['analyse_client_request','generate_content_plan','generate_campaign_plan','generate_social_posts','generate_email_copy','generate_blog_article_copy','generate_image_prompts','generate_video_scripts','qa_check_outputs']:
    text=Path(f'workflows/{wf}.json').read_text(errors='ignore')
    if 'Use prompt file ' in text:
        bad.append(wf)
if bad:
    print('Generic prompt-file references remain in generated LLM workflows:')
    print('\n'.join(bad))
    raise SystemExit(1)
print('llm prompt embedding ok')
PY

if rg -n "DELETE FROM|DROP TABLE|TRUNCATE|publish|send final|client deliver" workflows/*.json -i; then
  echo "Forbidden destructive/publish/send pattern found" >&2
  exit 1
fi

python - <<'PY'
import re, sys
from pathlib import Path
secret = re.compile(r'sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-')
scan_roots = ['workflows','docs','database','examples','tests','prompts','schemas']
files = []
for root in scan_roots:
    p = Path(root)
    if p.exists(): files.extend([x for x in p.rglob('*') if x.is_file()])
for extra in ['.env.example','README.md']:
    p = Path(extra)
    if p.exists(): files.append(p)
matches=[]
for p in files:
    text=p.read_text(errors='ignore')
    if secret.search(text): matches.append(str(p))
if matches:
    print('Potential hardcoded secret found:')
    print('\n'.join(matches))
    sys.exit(1)
print('secret scan ok')
PY

for v in POSTGRES_HOST POSTGRES_PORT POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD GOOGLE_DRIVE_CREDENTIAL_ID DEFAULT_PARENT_DRIVE_FOLDER_ID GOOGLE_DRIVE_ACCESS_TOKEN AGENT_WEBHOOK_SECRET NOTIFICATION_WEBHOOK_URL OPENAI_API_KEY OPENAI_MODEL LITELLM_BASE_URL LITELLM_API_KEY; do
  rg -q "^${v}=" .env.example
done

echo "validation ok"
