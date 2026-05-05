#!/usr/bin/env python3
"""Pre-n8n readiness checks for the AI Content n8n System."""
from __future__ import annotations
import json, re, subprocess, sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / 'workflows'
ENV_EXAMPLE = ROOT / '.env.example'
LLM_WORKFLOWS = ['analyse_client_request','generate_content_plan','generate_campaign_plan','generate_social_posts','generate_email_copy','generate_blog_article_copy','generate_image_prompts','generate_video_scripts','qa_check_outputs']
DRIVE_WORKFLOWS = ['create_new_drive_project_folder','create_standard_folder_structure','scan_drive_assets','parse_and_summarise_documents','create_asset_index','generate_delivery_pack']
REQUIRED_ENV = ['POSTGRES_HOST','POSTGRES_PORT','POSTGRES_DB','POSTGRES_USER','POSTGRES_PASSWORD','GOOGLE_DRIVE_CREDENTIAL_ID','DEFAULT_PARENT_DRIVE_FOLDER_ID','OPENAI_API_KEY','OPENAI_MODEL','LITELLM_BASE_URL','LITELLM_API_KEY','AGENT_WEBHOOK_SECRET','NOTIFICATION_WEBHOOK_URL']
FORBIDDEN = re.compile(r'DELETE FROM|DROP TABLE|TRUNCATE|send final|client deliver|publish', re.I)
SECRET_PATTERNS = re.compile(r'sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-')
BAD_EXPR = re.compile(r"\|\|\s*}}|(?<!\{)\{\$json|(?<!\{)\{\$env|(?<!\{)\{\$node|\$json\.body\.job_id\s*\|\||template action|NULLIF\('(?<!\{)\{\$json")
failures=[]
def fail(m): failures.append(m)
def run_generators():
    subprocess.run([sys.executable, str(ROOT/'scripts/build_llm_workflows.py')], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(ROOT/'scripts/embed_llm_prompts.py')], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(ROOT/'scripts/build_drive_workflows.py')], check=True, stdout=subprocess.DEVNULL)
    subprocess.run([sys.executable, str(ROOT/'scripts/fix_generated_n8n_expressions.py')], check=True, stdout=subprocess.DEVNULL)
def load(name):
    p=WORKFLOWS/f'{name}.json'
    if not p.exists(): fail(f'Missing workflow: {p}'); return {},''
    text=p.read_text()
    try: data=json.loads(text)
    except Exception as e: fail(f'Invalid JSON in {p}: {e}'); return {},text
    return data,text
def node_types(data): return {n.get('type','') for n in data.get('nodes',[])}
def common(name,text):
    if BAD_EXPR.search(text): fail(f'Malformed n8n expression/template marker in {name}')
    if FORBIDDEN.search(text): fail(f'Forbidden destructive/send/publish term found in {name}')
    if SECRET_PATTERNS.search(text): fail(f'Possible hardcoded secret found in {name}')
    if 'x-agent-secret' not in text and 'X-Agent-Secret' not in text: fail(f'Workflow lacks agent secret check: {name}')
def main():
    run_generators()
    env=ENV_EXAMPLE.read_text() if ENV_EXAMPLE.exists() else ''
    for k in REQUIRED_ENV:
        if f'{k}=' not in env: fail(f'Missing .env.example placeholder: {k}')
    for p in sorted(WORKFLOWS.glob('*.json')):
        text=p.read_text();
        try: json.loads(text)
        except Exception as e: fail(f'Invalid workflow JSON {p.name}: {e}')
        common(p.name,text)
    for name in LLM_WORKFLOWS:
        data,text=load(name); common(name,text); types=node_types(data)
        if 'n8n-nodes-base.httpRequest' not in types: fail(f'LLM workflow lacks HTTP Request node: {name}')
        if 'OPENAI_API_KEY' not in text and 'LITELLM_API_KEY' not in text: fail(f'LLM workflow lacks model credential env reference: {name}')
        if 'LITELLM_BASE_URL' not in text and 'api.openai.com' not in text: fail(f'LLM workflow lacks model endpoint reference: {name}')
        if 'INSERT INTO content_outputs' not in text: fail(f'LLM workflow does not persist content_outputs: {name}')
        if 'content_errors' not in text: fail(f'LLM workflow lacks content_errors failure path marker: {name}')
        if 'Use prompt file ' in text: fail(f'LLM workflow still uses generic prompt-file pointer: {name}')
    for name in DRIVE_WORKFLOWS:
        data,text=load(name); common(name,text); types=node_types(data)
        if 'n8n-nodes-base.googleDrive' not in types and 'n8n-nodes-base.httpRequest' not in types: fail(f'Drive workflow lacks Google Drive or HTTP Request node: {name}')
        if 'GOOGLE_DRIVE' not in text and 'DEFAULT_PARENT_DRIVE_FOLDER_ID' not in text and 'drive' not in text.lower(): fail(f'Drive workflow lacks Drive credential/config marker: {name}')
    if failures:
        print('Pre-n8n readiness check FAILED:\n')
        for x in failures: print(f'- {x}')
        return 1
    print('Pre-n8n readiness check passed.')
    return 0
if __name__=='__main__': sys.exit(main())
