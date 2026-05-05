#!/usr/bin/env python3
import json,re
from pathlib import Path
for path in sorted(Path('workflows').glob('*.json')):
    data=json.loads(path.read_text())
    text=path.read_text()
    paths=[n.get('parameters',{}).get('path','') for n in data.get('nodes',[]) if n.get('type')=='n8n-nodes-base.webhook']
    tables=sorted(set(re.findall(r'\b(content_[a-z_]+|client_profiles|job_messages)\b', text)))
    malformed=bool(re.search(r'\|\|\s*}}|\{\$json|\$json\.body\.job_id\s*\|\||template action', text))
    print(f'{path.name}: paths={paths}; tables={tables}; inserts_outputs={"INSERT INTO content_outputs" in text}; malformed={malformed}')
    if malformed:
        raise SystemExit(f'Malformed/placeholder terms found in {path}')
