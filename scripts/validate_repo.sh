#!/usr/bin/env bash
set -euo pipefail

ACTIVE_DIR="workflows/active"
ARCHIVE_DIR="workflows/archive/v1_debug_build"

required_workflows=(
  ai_content_orchestrator
  tool_job_intake
  tool_drive_assets
  tool_request_analysis
  tool_content_planning
  tool_content_generation
  tool_qa_delivery
  tool_logging
  api_supervisor_gateway
  api_human_review_gateway
)

for wf in "${required_workflows[@]}"; do
  test -f "${ACTIVE_DIR}/${wf}.json"
  python -m json.tool "${ACTIVE_DIR}/${wf}.json" >/dev/null
  rg -q 'x-agent-secret|X-Agent-Secret' "${ACTIVE_DIR}/${wf}.json"
done

active_count=$(find "${ACTIVE_DIR}" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')
if [ "$active_count" -gt 14 ]; then
  echo "Too many active workflows: ${active_count}" >&2
  exit 1
fi

test -d "$ARCHIVE_DIR"
archived_count=$(find "$ARCHIVE_DIR" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')
if [ "$archived_count" -lt 35 ]; then
  echo "Expected archived v1 debug workflows; found ${archived_count}" >&2
  exit 1
fi

for f in schemas/*.json examples/*.json tests/payloads/*.json; do python -m json.tool "$f" >/dev/null; done

test -f docs/tool_registry.md
test -f docs/deployment_model.md
test -f schemas/tool_registry.schema.json
test -f examples/tool_registry.example.json

python - <<'PY'
import json, pathlib, re, sys
root=pathlib.Path('workflows/active')
required={'ai_content_orchestrator','tool_job_intake','tool_drive_assets','tool_request_analysis','tool_content_planning','tool_content_generation','tool_qa_delivery','tool_logging','api_supervisor_gateway'}
found={p.stem for p in root.glob('*.json')}
missing=required-found
assert not missing, f'missing active workflows: {missing}'
for p in root.glob('*.json'):
    json.loads(p.read_text())
orch=(root/'ai_content_orchestrator.json').read_text()
for tool in ['tool_job_intake','tool_drive_assets','tool_request_analysis','tool_content_planning','tool_content_generation','tool_qa_delivery','tool_logging']:
    assert tool in orch, f'orchestrator does not reference {tool}'
text='\n'.join(p.read_text() for p in root.glob('*.json'))
for table in ['content_jobs','content_assets','content_outputs','content_tasks','content_events','content_errors','content_approvals','client_profiles','job_messages']:
    assert table in pathlib.Path('database/schema.sql').read_text(), f'missing schema table {table}'
for stage in ['waiting_for_analysis_approval','waiting_for_plan_approval','waiting_for_human_review','final_delivery']:
    assert stage in text, f'missing approval/status marker {stage}'
assert "reviewer_type='human'" in text or "reviewer_type = 'human'" in text or "'human'" in (root/'tool_qa_delivery.json').read_text(), 'final approval is not human-gated'
for status in ['created','intake_complete','assets_scanning','assets_parsed','analysis_complete','waiting_for_analysis_approval','waiting_for_plan_approval','generating_outputs','qa_in_progress','waiting_for_human_review','delivery_ready','completed','failed','paused','cancelled']:
    assert status in pathlib.Path('docs/architecture.md').read_text(), f'status not documented: {status}'
PY

python - <<'PY'
import re, sys
from pathlib import Path
bad = re.compile(r"\|\|\s*}}|(?<!\{)\{\$json|(?<!\{)\{\$env|(?<!\{)\{\$node|\$json\.body\.job_id\s*\|\||template action|NULLIF\('(?<!\{)\{\$json")
fail=[]
for p in Path('workflows/active').glob('*.json'):
    text=p.read_text(errors='ignore')
    if bad.search(text): fail.append(str(p))
if fail:
    print('Malformed expression or template-only action found:')
    print('\n'.join(fail))
    sys.exit(1)
PY

if rg -n "DELETE FROM|DROP TABLE|TRUNCATE|publish content|send final|final client deliverables|change credentials|modify database schema|edit n8n workflows directly" workflows/active/*.json -i; then
  echo "Forbidden destructive/publish/send pattern found in active workflows" >&2
  exit 1
fi

python - <<'PY'
import re, sys
from pathlib import Path
secret = re.compile(r'sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-')
scan_roots = ['workflows/active','docs','database','examples','tests','prompts','schemas']
files=[]
for root in scan_roots:
    p=Path(root)
    if p.exists(): files.extend([x for x in p.rglob('*') if x.is_file()])
for extra in ['.env.example','README.md']:
    p=Path(extra)
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

test -f tests/payloads/01_orchestrator_dry_run_job.json
test -f tests/payloads/02_supervisor_status_check.json
test -f tests/payloads/03_human_analysis_approval.json
test -f tests/payloads/04_generation_route.json
test -f tests/payloads/05_qa_delivery_route.json
rg -q "workflows/active" scripts/n8n_import_preflight.sh
rg -q "sandbox" tests/sandbox_test_plan.md

echo "validation ok"
