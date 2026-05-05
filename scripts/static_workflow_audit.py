#!/usr/bin/env python3
import json,glob,re
for fp in sorted(glob.glob('workflows/*.json')):
    d=json.load(open(fp))
    txt=json.dumps(d)
    path=''
    for n in d.get('nodes',[]):
        if n.get('type')=='n8n-nodes-base.webhook': path=n.get('parameters',{}).get('path','')
    tables=sorted(set(re.findall(r'content_[a-z_]+|job_messages|client_profiles',txt)))
    gates=[g for g in ['analysis','plan','final_delivery'] if f"approval_stage='{g}'" in txt]
    placeholders=[p for p in ['TODO','placeholder'] if p.lower() in txt.lower()]
    print(f"{fp}: webhook={path} tables={','.join(tables)} gates={','.join(gates) or '-'} placeholders={','.join(placeholders) or '-'}")
