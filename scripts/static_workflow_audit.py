#!/usr/bin/env python3
"""Static audit for the operator-ready n8n workflow set."""
from __future__ import annotations
import json
import re
import sys
from pathlib import Path

ACTIVE = Path('workflows/active')
ARCHIVE = Path('workflows/archive/v1_debug_build')
REQUIRED = {
    'ai_content_orchestrator', 'tool_job_intake', 'tool_drive_assets', 'tool_request_analysis',
    'tool_content_planning', 'tool_content_generation', 'tool_qa_delivery', 'tool_logging',
    'api_supervisor_gateway', 'api_human_review_gateway'
}
TOOL_WORKFLOWS = sorted(w for w in REQUIRED if w.startswith('tool_'))
LLM_TOOLS = ['tool_request_analysis', 'tool_content_planning', 'tool_content_generation', 'tool_qa_delivery']
BAD_EXPR = re.compile(r"\|\|\s*}}|(?<!\{)\{\$json|\{\{\$json\.[A-Za-z0-9_]+\}(?!\})|\$json\.body\.job_id\s*\|\||template action|NULLIF\('(?<!\{)\{\$json")
FORBIDDEN_ACTIVE_TARGETS = {
    'create_content_job','register_existing_drive_folder','create_new_drive_project_folder','create_standard_folder_structure',
    'scan_drive_assets','parse_and_summarise_documents','describe_images','handle_audio_video_references','create_asset_index',
    'analyse_client_request','generate_content_plan','route_output_tasks','generate_campaign_plan','generate_social_posts',
    'generate_email_copy','generate_blog_article_copy','generate_image_prompts','generate_video_scripts','qa_check_outputs',
    'generate_delivery_pack','notify_user_for_review','wait_for_human_approval'
}
REQUIRED_OUTPUT_TYPES = ['campaign_plan','social_posts','email_copy','blog_article','image_prompts','video_scripts']

def fail(message: str) -> None:
    print(f'AUDIT FAILURE: {message}', file=sys.stderr)
    raise SystemExit(1)

def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f'Invalid workflow JSON {path}: {exc}')

def code_nodes(data: dict):
    for node in data.get('nodes', []):
        if node.get('type') == 'n8n-nodes-base.code':
            yield node.get('name', '<unnamed>'), node.get('parameters', {}).get('jsCode', '')

def has_auth_compare(js: str) -> bool:
    return 'AGENT_WEBHOOK_SECRET' in js and 'x-agent-secret' in js and re.search(r'secret\s*!==\s*expected|expected\s*!==\s*secret|secret\s*===\s*expected|expected\s*===\s*secret', js)

def likely_unreachable(js: str) -> bool:
    depth = 0
    lines = js.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith('//'):
            continue
        before_depth = depth
        # crude but effective for these workflow code snippets
        if re.search(r'(^|[;\s])return\b', stripped) and before_depth == 0:
            tail = lines[idx + 1:]
            for later in tail:
                later = later.strip()
                if later and not later.startswith('//'):
                    return True
        depth += line.count('{') - line.count('}')
        if depth < 0:
            depth = 0
    return False

def main() -> int:
    if not ACTIVE.exists():
        fail('workflows/active does not exist')
    active_files = sorted(ACTIVE.glob('*.json'))
    active_count = len(active_files)
    if not (8 <= active_count <= 14):
        fail(f'active workflow count must be between 8 and 14, found {active_count}')
    if len(list(ARCHIVE.glob('*.json'))) < 35:
        fail('archived v1 debug workflows are missing or incomplete')
    found = {p.stem for p in active_files}
    missing = REQUIRED - found
    if missing:
        fail(f'Missing active workflows: {sorted(missing)}')

    all_text = ''
    summaries = []
    for path in active_files:
        data = load(path)
        text = path.read_text()
        all_text += '\n' + text
        if BAD_EXPR.search(text):
            fail(f'Malformed expression or placeholder action in {path}')
        auth_nodes = [js for _, js in code_nodes(data) if 'x-agent-secret' in js or 'X-Agent-Secret' in js]
        if not auth_nodes or not any(has_auth_compare(js) for js in auth_nodes):
            fail(f'{path.name} does not compare x-agent-secret with AGENT_WEBHOOK_SECRET')
        for node_name, js in code_nodes(data):
            if likely_unreachable(js):
                fail(f'{path.name} code node {node_name!r} has likely unreachable code after unconditional return')
        execute_targets = [json.dumps(n.get('parameters', {})) for n in data.get('nodes', []) if n.get('type') == 'n8n-nodes-base.executeWorkflow']
        for target in FORBIDDEN_ACTIVE_TARGETS:
            if any(target in call for call in execute_targets):
                fail(f'{path.name} references archived v1 workflow as active execute target: {target}')
        webhook_paths = [n.get('parameters', {}).get('path', '') for n in data.get('nodes', []) if n.get('type') == 'n8n-nodes-base.webhook']
        tables = sorted(set(re.findall(r'\b(content_[a-z_]+|client_profiles|job_messages)\b', text)))
        summaries.append({'workflow': path.name, 'webhook_paths': webhook_paths, 'tables': tables, 'auth_compares_env_secret': True})

    orch = (ACTIVE / 'ai_content_orchestrator.json').read_text()
    for tool in TOOL_WORKFLOWS:
        if tool not in orch:
            fail(f'Orchestrator does not call {tool}')
    for marker in ['desired_tools','tool_results','current_stage','payload','dry_run_full_lifecycle']:
        if marker not in orch:
            fail(f'Orchestrator missing state/routing marker: {marker}')

    generation = (ACTIVE / 'tool_content_generation.json').read_text()
    for output_type in REQUIRED_OUTPUT_TYPES:
        if output_type not in generation:
            fail(f'content generation dispatch missing output type: {output_type}')
    if 'generated_output_json' not in generation or 'choices?.[0]?.message?.content' not in generation:
        fail('content generation does not parse/store LLM response before persistence')

    for name in LLM_TOOLS:
        text = (ACTIVE / f'{name}.json').read_text()
        if 'Parse LLM Response' not in text or 'choices?.[0]?.message?.content' not in text:
            fail(f'{name} lacks OpenAI/LiteLLM response parsing')
        if 'INSERT INTO content_outputs' in text and '_json' not in text:
            fail(f'{name} inserts content_outputs without parsed JSON field')
        if 'content_errors' not in text:
            fail(f'{name} lacks parse warning/error logging marker')

    required_gate_markers = [
        "approval_stage='analysis'", "approval_stage='plan'", "approval_stage='final_delivery'",
        "reviewer_type='human'", 'waiting_for_analysis_approval', 'waiting_for_plan_approval', 'waiting_for_human_review'
    ]
    for marker in required_gate_markers:
        if marker not in all_text:
            fail(f'Missing approval gate marker: {marker}')
    supervisor = (ACTIVE / 'api_supervisor_gateway.json').read_text()
    for forbidden in ['delete_files','publish_content','send_final','change_credentials','modify_schema','edit_workflows','approve_final_delivery']:
        if forbidden not in supervisor:
            fail(f'supervisor safety boundary missing forbidden action: {forbidden}')

    for summary in summaries:
        print(summary)
    print('static workflow audit passed')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
