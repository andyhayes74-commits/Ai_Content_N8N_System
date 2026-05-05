#!/usr/bin/env python3
import json
import re
from pathlib import Path

BAD = re.compile(r"\|\|\s*}}|(?<!\{)\{\$json|\$json\.body\.job_id\s*\|\||template action|NULLIF\('(?<!\{)\{\$json")

for path in sorted(Path('workflows').glob('*.json')):
    data = json.loads(path.read_text())
    text = path.read_text()
    webhook_paths = [
        n.get('parameters', {}).get('path', '')
        for n in data.get('nodes', [])
        if n.get('type') == 'n8n-nodes-base.webhook'
    ]
    tables = sorted(set(re.findall(r'\b(content_[a-z_]+|client_profiles|job_messages)\b', text)))
    summary = {
        'workflow': path.name,
        'webhook_paths': webhook_paths,
        'tables': tables,
        'auth_header': 'x-agent-secret' in text or 'X-Agent-Secret' in text,
        'approval_gate': 'content_approvals' in text,
        'inserts_outputs': 'INSERT INTO content_outputs' in text,
        'http_request': 'n8n-nodes-base.httpRequest' in text,
        'google_drive': 'n8n-nodes-base.googleDrive' in text,
        'malformed': bool(BAD.search(text)),
    }
    print(summary)
    if summary['malformed']:
        raise SystemExit(f'Malformed expression or placeholder action in {path}')
