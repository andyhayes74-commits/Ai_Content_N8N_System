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
  rg -q 'AGENT_WEBHOOK_SECRET' "${ACTIVE_DIR}/${wf}.json"
  rg -q 'secret !== expected|secret === expected|expected !== secret|expected === secret' "${ACTIVE_DIR}/${wf}.json"
done

active_count=$(find "${ACTIVE_DIR}" -maxdepth 1 -type f -name '*.json' | wc -l | tr -d ' ')
if [ "$active_count" -lt 8 ] || [ "$active_count" -gt 14 ]; then
  echo "Active workflow count must be between 8 and 14; found ${active_count}" >&2
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

python scripts/static_workflow_audit.py >/dev/null
python scripts/pre_n8n_readiness_check.py >/dev/null

python - <<'PY'
import pathlib
sql=pathlib.Path('database/schema.sql').read_text()
required=['content_jobs','content_assets','content_outputs','content_tasks','content_events','content_errors','content_approvals','client_profiles','job_messages']
missing=[t for t in required if t not in sql]
assert not missing, missing
assert 'reviewer_type' in sql, 'content_approvals.reviewer_type missing'
print('schema check ok')
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

for fixture in \
  tests/payloads/01_orchestrator_dry_run_job.json \
  tests/payloads/02_supervisor_status_check.json \
  tests/payloads/03_human_analysis_approval.json \
  tests/payloads/04_generation_route.json \
  tests/payloads/05_qa_delivery_route.json; do
  test -f "$fixture"
done

rg -q 'ACTIVE_DIR="workflows/active"' scripts/n8n_import_preflight.sh
if rg -n 'n8n import:workflow.*--input=workflows/?($|\s)' scripts/n8n_import_preflight.sh; then
  echo "Import preflight must not target workflows/ root" >&2
  exit 1
fi
rg -q "GitHub is the source of truth" docs/deployment_model.md
rg -q "n8n is the runtime" docs/deployment_model.md
rg -q "No live n8n runtime" docs/pre_n8n_completion_report.md

echo "validation ok"
