#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python 3 is required for repository validation." >&2
    exit 1
  fi
fi

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
  "$PYTHON_BIN" -m json.tool "${ACTIVE_DIR}/${wf}.json" >/dev/null
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

for f in schemas/*.json examples/*.json tests/payloads/*.json registry/*.json; do
  "$PYTHON_BIN" -m json.tool "$f" >/dev/null
done

test ! -f .env.example
test -f docs/tool_registry.md
test -f docs/deployment_model.md
test -f docs/system_source_of_truth.md
test -f docs/v2_development_plan.md
test -f docs/v2_build_roadmap.md
test -f schemas/tool_registry.schema.json
test -f examples/tool_registry.example.json
test -f registry/tools.active.json
test -f registry/infrastructure_workflows.json
test -f scripts/deploy-n8n-workflows.mjs
node --check scripts/deploy-n8n-workflows.mjs >/dev/null

"$PYTHON_BIN" scripts/validate_tool_registry.py >/dev/null
"$PYTHON_BIN" scripts/static_workflow_audit.py >/dev/null
"$PYTHON_BIN" scripts/pre_n8n_readiness_check.py >/dev/null
DRY_RUN=true node scripts/deploy-n8n-workflows.mjs >/dev/null

"$PYTHON_BIN" - <<'PY'
import pathlib
sql=pathlib.Path('database/schema.sql').read_text()
required=['content_jobs','content_assets','content_outputs','content_tasks','content_events','content_errors','content_approvals','client_profiles','job_messages']
missing=[t for t in required if t not in sql]
assert not missing, missing
assert 'reviewer_type' in sql, 'content_approvals.reviewer_type missing'
print('schema check ok')
PY

"$PYTHON_BIN" - <<'PY'
import json
import re
import sys
from pathlib import Path

active_text = "\n".join(p.read_text() for p in Path('workflows/active').glob('*.json'))
forbidden = re.compile(r'DELETE FROM|DROP TABLE|TRUNCATE|publish content|send final|final client deliverables|change credentials|modify database schema|edit n8n workflows directly', re.I)
if forbidden.search(active_text):
    print('Forbidden destructive/publish/send pattern found in active workflows', file=sys.stderr)
    sys.exit(1)
if '$env' in active_text:
    print('Active workflows must not use environment variables; use n8n credentials or payload fields', file=sys.stderr)
    sys.exit(1)
secret = re.compile(r'sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-')
scan_roots = ['workflows/active','docs','database','examples','tests','prompts','schemas']
files=[]
for root in scan_roots:
    p=Path(root)
    if p.exists():
        files.extend([x for x in p.rglob('*') if x.is_file()])
for extra in ['README.md']:
    p=Path(extra)
    if p.exists():
        files.append(p)
matches=[str(p) for p in files if secret.search(p.read_text(errors='ignore'))]
if matches:
    print('Potential hardcoded secret found:')
    print('\n'.join(matches))
    sys.exit(1)
print('secret and env scan ok')
PY

for fixture in \
  tests/payloads/01_orchestrator_dry_run_job.json \
  tests/payloads/02_supervisor_status_check.json \
  tests/payloads/03_human_analysis_approval.json \
  tests/payloads/04_generation_route.json \
  tests/payloads/05_qa_delivery_route.json; do
  test -f "$fixture"
done

"$PYTHON_BIN" - <<'PY'
import re
from pathlib import Path
text = Path('scripts/n8n_import_preflight.sh').read_text()
assert 'ACTIVE_DIR="workflows/active"' in text
assert not re.search(r'n8n import:workflow.*--input=workflows/?($|\s)', text)
docs = Path('docs/deployment_model.md').read_text()
assert 'GitHub is the source of truth' in docs
assert 'n8n is the runtime' in docs
PY

echo "validation ok"
