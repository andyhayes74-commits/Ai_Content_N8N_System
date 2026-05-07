#!/usr/bin/env python3
import json
import re
from pathlib import Path

ACTIVE = Path('workflows/active')
BAD = re.compile(r"\|\|\s*}}|(?<!\{)\{\$json|\$json\.body\.job_id\s*\|\||template action|NULLIF\('(?<!\{)\{\$json")
REQUIRED = {
    'ai_content_orchestrator', 'tool_job_intake', 'tool_drive_assets', 'tool_request_analysis',
    'tool_content_planning', 'tool_content_generation', 'tool_qa_delivery', 'tool_logging',
    'api_supervisor_gateway', 'api_human_review_gateway'
}
found = {p.stem for p in ACTIVE.glob('*.json')}
missing = REQUIRED - found
if missing:
    raise SystemExit(f'Missing active workflows: {sorted(missing)}')
for path in sorted(ACTIVE.glob('*.json')):
    data = json.loads(path.read_text())
    text = path.read_text()
    webhook_paths = [n.get('parameters', {}).get('path', '') for n in data.get('nodes', []) if n.get('type') == 'n8n-nodes-base.webhook']
    execute_calls = [json.dumps(n.get('parameters', {})) for n in data.get('nodes', []) if n.get('type') == 'n8n-nodes-base.executeWorkflow']
    tables = sorted(set(re.findall(r'\b(content_[a-z_]+|client_profiles|job_messages)\b', text)))
    summary = {
        'workflow': path.name,
        'webhook_paths': webhook_paths,
        'execute_workflow_calls': execute_calls,
        'tables': tables,
        'auth_header': 'x-agent-secret' in text or 'X-Agent-Secret' in text,
        'approval_gate': 'content_approvals' in text or 'approval_gate' in text,
        'final_human_gate': 'final_delivery' in text and 'human' in text,
        'http_request': 'n8n-nodes-base.httpRequest' in text,
        'google_drive': 'n8n-nodes-base.googleDrive' in text,
        'malformed': bool(BAD.search(text)),
    }
    print(summary)
    if summary['malformed']:
        raise SystemExit(f'Malformed expression or placeholder action in {path}')
orch = (ACTIVE / 'ai_content_orchestrator.json').read_text()
for tool in sorted(REQUIRED - {'ai_content_orchestrator','api_supervisor_gateway','api_human_review_gateway'}):
    if tool not in orch:
        raise SystemExit(f'Orchestrator does not call {tool}')
print('static workflow audit passed')
