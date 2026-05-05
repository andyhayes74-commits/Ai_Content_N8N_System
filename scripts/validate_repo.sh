#!/usr/bin/env bash
set -euo pipefail
required_workflows=(create_content_job api_approve_analysis api_approve_plan api_approve_final_delivery generate_content_plan route_output_tasks generate_social_posts qa_check_outputs generate_delivery_pack retry_safe_failed_steps)
for wf in "${required_workflows[@]}"; do
  test -f "workflows/${wf}.json"
  python -m json.tool "workflows/${wf}.json" >/dev/null
  rg -q '"path": "v1/' "workflows/${wf}.json"
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
rg -q "INSERT INTO content_approvals" workflows/api_approve_analysis.json
rg -q "INSERT INTO content_approvals" workflows/api_approve_plan.json
rg -q "final_delivery" workflows/api_approve_final_delivery.json
rg -q "reviewer_type" workflows/api_approve_final_delivery.json
rg -q "INSERT INTO content_outputs" workflows/generate_content_plan.json
rg -q "INSERT INTO content_outputs" workflows/generate_social_posts.json
rg -q "INSERT INTO content_outputs" workflows/qa_check_outputs.json
rg -q "UPDATE content_outputs" workflows/qa_check_outputs.json
rg -q "delivery_ready" workflows/generate_delivery_pack.json
if rg -n "DELETE FROM|DROP TABLE|TRUNCATE|publish|send final|client deliver" workflows/*.json -i; then
  echo "Forbidden destructive/publish/send pattern found" >&2
  exit 1
fi
if rg -n "sk-[A-Za-z0-9]|AIza|xox[baprs]-" .; then
  echo "Potential hardcoded secret found" >&2
  exit 1
fi
echo "validation ok"
