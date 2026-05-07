#!/usr/bin/env python3
"""Pre-n8n readiness checks for the repaired operator-ready system."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / 'workflows' / 'active'
ARCHIVE = ROOT / 'workflows' / 'archive' / 'v1_debug_build'
ENV_EXAMPLE = ROOT / '.env.example'
REQUIRED_WORKFLOWS = ['ai_content_orchestrator','tool_job_intake','tool_drive_assets','tool_request_analysis','tool_content_planning','tool_content_generation','tool_qa_delivery','tool_logging','api_supervisor_gateway','api_human_review_gateway']
REQUIRED_ENV = ['POSTGRES_HOST','POSTGRES_PORT','POSTGRES_DB','POSTGRES_USER','POSTGRES_PASSWORD','GOOGLE_DRIVE_CREDENTIAL_ID','DEFAULT_PARENT_DRIVE_FOLDER_ID','GOOGLE_DRIVE_ACCESS_TOKEN','OPENAI_API_KEY','OPENAI_MODEL','LITELLM_BASE_URL','LITELLM_API_KEY','AGENT_WEBHOOK_SECRET','NOTIFICATION_WEBHOOK_URL']
FORBIDDEN = re.compile(r'DELETE FROM|DROP TABLE|TRUNCATE|publish content|send final|final client deliverables|change credentials|modify database schema|edit n8n workflows directly', re.I)
SECRET_PATTERNS = re.compile(r'sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-')
failures=[]
def fail(m): failures.append(m)
def load(name):
    p=ACTIVE/f'{name}.json'
    if not p.exists(): fail(f'Missing workflow: {p}'); return {},''
    text=p.read_text()
    try: data=json.loads(text)
    except Exception as e: fail(f'Invalid JSON in {p}: {e}'); return {},text
    return data,text
def node_types(data): return {n.get('type','') for n in data.get('nodes',[])}
def main():
    env=ENV_EXAMPLE.read_text() if ENV_EXAMPLE.exists() else ''
    for k in REQUIRED_ENV:
        if f'{k}=' not in env: fail(f'Missing .env.example placeholder: {k}')
    active_count=len(list(ACTIVE.glob('*.json')))
    if not 8 <= active_count <= 14: fail(f'Active workflow count outside 8-14: {active_count}')
    if len(list(ARCHIVE.glob('*.json'))) < 35: fail('v1 debug workflows are not archived')
    for name in REQUIRED_WORKFLOWS:
        data,text=load(name)
        if FORBIDDEN.search(text): fail(f'Forbidden destructive/send/publish term found in {name}')
        if SECRET_PATTERNS.search(text): fail(f'Possible hardcoded secret found in {name}')
        if 'AGENT_WEBHOOK_SECRET' not in text or not re.search(r'secret\s*!==\s*expected|secret\s*===\s*expected|expected\s*!==\s*secret|expected\s*===\s*secret', text):
            fail(f'Workflow does not compare x-agent-secret against AGENT_WEBHOOK_SECRET: {name}')
    audit = subprocess.run([sys.executable, str(ROOT/'scripts/static_workflow_audit.py')], cwd=ROOT, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if audit.returncode != 0:
        fail('static workflow audit failed:\n' + audit.stdout + audit.stderr)
    orch=(ACTIVE/'ai_content_orchestrator.json').read_text() if (ACTIVE/'ai_content_orchestrator.json').exists() else ''
    for marker in ['desired_tools','tool_results','current_stage','dry_run_full_lifecycle']:
        if marker not in orch: fail(f'Orchestrator missing state/routing marker: {marker}')
    for name in ['tool_request_analysis','tool_content_planning','tool_content_generation','tool_qa_delivery']:
        data,text=load(name); types=node_types(data)
        if 'n8n-nodes-base.httpRequest' not in types: fail(f'LLM-capable tool lacks HTTP Request node: {name}')
        if 'OPENAI_API_KEY' not in text and 'LITELLM_API_KEY' not in text: fail(f'LLM-capable tool lacks model credential env reference: {name}')
        if 'Parse LLM Response' not in text or 'choices?.[0]?.message?.content' not in text: fail(f'LLM-capable tool does not parse chat completion response: {name}')
        if 'content_errors' not in text: fail(f'LLM-capable tool lacks parse warning/error logging: {name}')
    for name in ['tool_drive_assets','tool_qa_delivery']:
        data,text=load(name); types=node_types(data)
        if 'n8n-nodes-base.googleDrive' not in types: fail(f'Drive tool lacks Google Drive node: {name}')
    all_text='\n'.join((ACTIVE/f'{n}.json').read_text() for n in REQUIRED_WORKFLOWS if (ACTIVE/f'{n}.json').exists())
    for marker in ['waiting_for_analysis_approval','waiting_for_plan_approval','waiting_for_human_review','final_delivery','reviewer_type']:
        if marker not in all_text: fail(f'Missing safety/approval marker: {marker}')
    for doc in ['docs/tool_registry.md','docs/deployment_model.md','docs/architecture.md','docs/failure_recovery.md','docs/pre_n8n_completion_report.md','docs/setup_guide.md']:
        if not (ROOT/doc).exists(): fail(f'Missing doc: {doc}')
    for fixture in ['tests/payloads/01_orchestrator_dry_run_job.json','tests/payloads/02_supervisor_status_check.json','tests/payloads/03_human_analysis_approval.json','tests/payloads/04_generation_route.json','tests/payloads/05_qa_delivery_route.json']:
        if not (ROOT/fixture).exists(): fail(f'Missing dry-run payload: {fixture}')
    import_text=(ROOT/'scripts/n8n_import_preflight.sh').read_text()
    if 'workflows/active' not in import_text or '--input=workflows/' in import_text: fail('n8n import preflight does not target workflows/active only')
    if failures:
        print('Pre-n8n readiness check FAILED:\n')
        for x in failures: print(f'- {x}')
        return 1
    print('Pre-n8n readiness check passed.')
    return 0
if __name__ == '__main__': sys.exit(main())
