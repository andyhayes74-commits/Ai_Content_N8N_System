#!/usr/bin/env python3
"""Generate live-mode-ready LLM workflows for the AI Content n8n System.

The generated workflows retain explicit dry-run fallback support, but live mode is the
normal path: Postgres context -> OpenAI/LiteLLM HTTP Request -> parse -> Postgres output.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"

CONFIG = {
    "analyse_client_request": ("request_analysis", "Request Analysis", "analyse_client_request", "prompts/request_analysis.md", None, "waiting_for_analysis_approval"),
    "generate_content_plan": ("content_plan", "Content Plan", "generate_content_plan", "prompts/content_plan.md", "analysis", "waiting_for_plan_approval"),
    "generate_campaign_plan": ("campaign_plan", "Campaign Plan", "campaign_plan", "prompts/campaign_plan.md", "plan", None),
    "generate_social_posts": ("social_posts", "Social Posts", "social_posts", "prompts/social_posts.md", "plan", None),
    "generate_email_copy": ("email_copy", "Email Copy", "email_copy", "prompts/email_copy.md", "plan", None),
    "generate_blog_article_copy": ("blog_article", "Blog / Article Copy", "blog_article", "prompts/blog_article.md", "plan", None),
    "generate_image_prompts": ("image_prompts", "Image Prompts", "image_prompts", "prompts/image_prompts.md", "plan", None),
    "generate_video_scripts": ("video_scripts", "Video Scripts", "video_scripts", "prompts/video_scripts.md", "plan", None),
    "qa_check_outputs": ("qa_report", "QA Report", "qa_check_outputs", "prompts/qa_check.md", None, "waiting_for_human_review"),
}


def n(id_, name, type_, position, parameters, version=1):
    return {
        "id": str(id_),
        "name": name,
        "type": type_,
        "typeVersion": version,
        "position": position,
        "parameters": parameters,
    }


def workflow(name: str, output_type: str, title: str, task_key: str, prompt_file: str, approval_stage: str | None, status_after: str | None):
    gate_sql = "EXISTS (SELECT 1 FROM job)" if not approval_stage else f"EXISTS (SELECT 1 FROM content_approvals WHERE job_id=(SELECT id FROM job) AND approval_stage='{approval_stage}' AND decision='approved')"
    status_cte = ""
    if status_after:
        status_cte = f", job_update AS (UPDATE content_jobs SET status='{status_after}'::job_status, updated_at=now() WHERE id=NULLIF('{{$json.job_id}}','')::uuid RETURNING id)"
    load_context_query = f"""=WITH job AS (
  SELECT id, project_name, brief_text, requested_outputs, drive_root_folder_id
  FROM content_jobs
  WHERE id=NULLIF('{{$json.job_id}}','')::uuid
), gate AS (
  SELECT {gate_sql} AS is_allowed
), assets AS (
  SELECT COALESCE(jsonb_agg(jsonb_build_object('file_name', file_name, 'mime_type', mime_type, 'parse_status', parse_status, 'metadata', extracted_metadata)), '[]'::jsonb) AS asset_summary
  FROM content_assets WHERE job_id=(SELECT id FROM job)
), outputs AS (
  SELECT COALESCE(jsonb_agg(jsonb_build_object('output_type', output_type, 'title', title, 'qa_status', qa_status, 'structured_data', structured_data) ORDER BY created_at), '[]'::jsonb) AS prior_outputs
  FROM content_outputs WHERE job_id=(SELECT id FROM job)
)
SELECT (SELECT is_allowed FROM gate) AS allowed,
       (SELECT id::text FROM job) AS job_id,
       (SELECT project_name FROM job) AS project_name,
       (SELECT brief_text FROM job) AS brief_text,
       (SELECT requested_outputs::text FROM job) AS requested_outputs_json,
       (SELECT asset_summary::text FROM assets) AS asset_summary_json,
       (SELECT prior_outputs::text FROM outputs) AS prior_outputs_json;"""
    if name == "qa_check_outputs":
        load_context_query = """=WITH job AS (
  SELECT id, project_name, brief_text FROM content_jobs WHERE id=NULLIF('{{$json.job_id}}','')::uuid
), outputs AS (
  SELECT COALESCE(jsonb_agg(jsonb_build_object('id',id,'output_type',output_type,'title',title,'qa_status',qa_status,'structured_data',structured_data) ORDER BY created_at),'[]'::jsonb) AS pending_outputs
  FROM content_outputs WHERE job_id=(SELECT id FROM job) AND qa_status='pending'
)
SELECT EXISTS (SELECT 1 FROM job) AS allowed,
       (SELECT id::text FROM job) AS job_id,
       (SELECT project_name FROM job) AS project_name,
       (SELECT brief_text FROM job) AS brief_text,
       (SELECT pending_outputs::text FROM outputs) AS prior_outputs_json,
       '[]'::text AS requested_outputs_json,
       '[]'::text AS asset_summary_json;"""
    normalize = """const body=$json.body??$json;
const headers=$json.headers??{};
const fallback=body.generated_output||body.output||body.request_analysis||body.content_plan||body.qa_report||{mode:'dry_run_fallback',note:'Explicit dry_run fallback payload was not supplied'};
return [{json:{...body,job_id:body.job_id||$json.job_id||'',mode:body.mode||'live',fallback_payload:fallback,agent_secret:headers['x-agent-secret']||headers['X-Agent-Secret']||''}}];"""
    build_request = f"""const ctx=$json;
function safeJson(value, fallback) {{ try {{ return JSON.parse(value || ''); }} catch (e) {{ return fallback; }} }}
const prompt = `You are running workflow {name}. Use prompt file {prompt_file}. Return strict JSON only. Do not invent unsupported client facts. Separate facts, assumptions, missing information, risk flags, and source material used.`;
const userPayload = {{
  workflow: '{name}',
  output_type: '{output_type}',
  project_name: ctx.project_name,
  brief_text: ctx.brief_text,
  requested_outputs: safeJson(ctx.requested_outputs_json, []),
  assets: safeJson(ctx.asset_summary_json, []),
  prior_outputs: safeJson(ctx.prior_outputs_json, [])
}};
return [{{json:{{...ctx,model_request:{{model:$env.OPENAI_MODEL||'gpt-4o-mini',messages:[{{role:'system',content:prompt}},{{role:'user',content:JSON.stringify(userPayload)}}],temperature:0.2,response_format:{{type:'json_object'}}}}}}}}];"""
    dry = """const n=$node['Normalize Input'].json;
const ctx=$node['Load Context'].json;
const output=n.fallback_payload||{mode:'dry_run_fallback'};
const status=output.overall_status==='pass'?'passed':(output.overall_status==='fail'?'failed':'needs_human_review');
const outputSql=JSON.stringify(output).replace(/'/g,"''");
return [{json:{job_id:ctx.job_id, output_sql:outputSql, body_markdown_sql:'', qa_status:status, source:'dry_run_fallback', is_error:false}}];"""
    parse = """const ctx=$node['Load Context'].json;
const raw=$json;
let content=raw?.choices?.[0]?.message?.content||raw?.body?.choices?.[0]?.message?.content||'';
let parsed;
let isError=Boolean(raw.error||raw.message?.includes?.('error'));
try { parsed=typeof content==='string'&&content.trim()?JSON.parse(content):raw; } catch(e) { parsed={raw_text:content,parse_warning:'Model response was not valid JSON'}; }
const status=parsed.overall_status==='pass'?'passed':(parsed.overall_status==='fail'?'failed':'needs_human_review');
const outputSql=JSON.stringify(parsed).replace(/'/g,"''");
return [{json:{job_id:ctx.job_id, output_sql:outputSql, body_markdown_sql:String(content||'').replace(/'/g,"''"), qa_status:status, source:'llm_http', is_error:isError, error_message:raw.error?.message||raw.message||''}}];"""
    if name == "qa_check_outputs":
        store_query = f"""=WITH output_update AS (
  UPDATE content_outputs SET qa_status='{{$json.qa_status}}', updated_at=now()
  WHERE job_id=NULLIF('{{$json.job_id}}','')::uuid AND qa_status='pending'
  RETURNING id
), report_insert AS (
  INSERT INTO content_outputs (job_id, output_type, title, structured_data, qa_status)
  VALUES (NULLIF('{{$json.job_id}}','')::uuid,'qa_report','QA Report','{{$json.output_sql}}'::jsonb,'passed')
  RETURNING id
), job_update AS (
  UPDATE content_jobs SET status='waiting_for_human_review', updated_at=now()
  WHERE id=NULLIF('{{$json.job_id}}','')::uuid
  RETURNING id
), event_insert AS (
  INSERT INTO content_events (job_id,event_type,message,metadata)
  SELECT NULLIF('{{$json.job_id}}','')::uuid,'qa_completed','QA completed',jsonb_build_object('qa_report_id',(SELECT id FROM report_insert),'updated_outputs',(SELECT count(*) FROM output_update),'qa_status','{{$json.qa_status}}','source','{{$json.source}}')
)
SELECT (SELECT id::text FROM report_insert) AS output_id,(SELECT count(*) FROM output_update) AS updated_outputs;"""
    else:
        store_query = f"""=WITH output_insert AS (
  INSERT INTO content_outputs (job_id, output_type, title, structured_data, body_markdown, qa_status)
  VALUES (NULLIF('{{$json.job_id}}','')::uuid, '{output_type}', '{title}', '{{$json.output_sql}}'::jsonb, NULLIF('{{$json.body_markdown_sql}}',''), 'pending')
  RETURNING id
), task_update AS (
  UPDATE content_tasks SET status='completed', output_payload='{{$json.output_sql}}'::jsonb, updated_at=now()
  WHERE job_id=NULLIF('{{$json.job_id}}','')::uuid AND task_key='{task_key}'
  RETURNING id
){status_cte}, event_insert AS (
  INSERT INTO content_events (job_id,event_type,message,metadata)
  SELECT NULLIF('{{$json.job_id}}','')::uuid,'output_stored','Output stored: {output_type}',jsonb_build_object('output_id',(SELECT id FROM output_insert),'source','{{$json.source}}')
)
SELECT (SELECT id::text FROM output_insert) AS output_id;"""
    error_query = f"""=WITH err AS (
  INSERT INTO content_errors (job_id,severity,error_code,error_message,recoverable,context)
  VALUES (NULLIF('{{$json.job_id}}','')::uuid,'high','LLM_HTTP_ERROR',COALESCE(NULLIF('{{$json.error_message || ""}}',''),'LLM HTTP request failed'),true,jsonb_build_object('workflow','{name}'))
  RETURNING id
), event_insert AS (
  INSERT INTO content_events (job_id,event_type,message,metadata)
  SELECT NULLIF('{{$json.job_id}}','')::uuid,'llm_error_logged','LLM error logged',jsonb_build_object('error_id',(SELECT id FROM err))
)
SELECT id::text AS error_id FROM err;"""
    nodes = [
        n(1, "Webhook", "n8n-nodes-base.webhook", [0, 0], {"path": f"v1/{name}", "httpMethod": "POST", "responseMode": "responseNode"}),
        n(2, "Normalize Input", "n8n-nodes-base.code", [220, 0], {"jsCode": normalize}, 2),
        n(3, "Check Secret", "n8n-nodes-base.if", [440, 0], {"conditions": {"string": [{"value1": "={{$json.agent_secret}}", "operation": "equal", "value2": "={{$env.AGENT_WEBHOOK_SECRET}}"}]}}),
        n(4, "Reject Unauthorized", "n8n-nodes-base.respondToWebhook", [660, -180], {"respondWith": "json", "responseBody": "={\"ok\":false,\"error\":\"unauthorized\"}", "options": {"responseCode": 401}}),
        n(5, "Load Context", "n8n-nodes-base.postgres", [660, 0], {"operation": "executeQuery", "query": load_context_query}),
        n(6, "Is Allowed?", "n8n-nodes-base.if", [880, 0], {"conditions": {"boolean": [{"value1": "={{$json.allowed}}", "operation": "equal", "value2": True}]}}),
        n(7, "Reject Blocked", "n8n-nodes-base.respondToWebhook", [1100, -180], {"respondWith": "json", "responseBody": f"={{\"ok\":false,\"workflow\":\"{name}\",\"error\":\"approval_gate_blocked\"}}", "options": {"responseCode": 409}}),
        n(8, "Is Dry Run?", "n8n-nodes-base.if", [1100, 0], {"conditions": {"string": [{"value1": "={{$node[\"Normalize Input\"].json.mode}}", "operation": "equal", "value2": "dry_run"}]}}),
        n(9, "Build Dry Run Output", "n8n-nodes-base.code", [1320, -80], {"jsCode": dry}, 2),
        n(10, "Build Model Request", "n8n-nodes-base.code", [1320, 120], {"jsCode": build_request}, 2),
        n(11, "Call OpenAI or LiteLLM", "n8n-nodes-base.httpRequest", [1540, 120], {"method": "POST", "url": "={{($env.LITELLM_BASE_URL || 'https://api.openai.com/v1') + '/chat/completions'}}", "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Authorization", "value": "={{'Bearer ' + ($env.LITELLM_API_KEY || $env.OPENAI_API_KEY)}}"}, {"name": "Content-Type", "value": "application/json"}]}, "sendBody": True, "specifyBody": "json", "jsonBody": "={{JSON.stringify($json.model_request)}}", "options": {"timeout": 120000}}, 4),
        n(12, "Parse Model Response", "n8n-nodes-base.code", [1760, 120], {"jsCode": parse}, 2),
        n(13, "Model Call Failed?", "n8n-nodes-base.if", [1980, 80], {"conditions": {"boolean": [{"value1": "={{$json.is_error}}", "operation": "equal", "value2": True}]}}),
        n(14, "Store Output", "n8n-nodes-base.postgres", [2200, -60], {"operation": "executeQuery", "query": store_query}),
        n(15, "Store Model Error", "n8n-nodes-base.postgres", [2200, 180], {"operation": "executeQuery", "query": error_query}),
        n(16, "Respond Success", "n8n-nodes-base.respondToWebhook", [2420, -60], {"respondWith": "json", "responseBody": f"={{\"ok\":true,\"workflow\":\"{name}\",\"output_id\":\"{{$json.output_id}}\"}}", "options": {"responseCode": 200}}),
        n(17, "Respond Error", "n8n-nodes-base.respondToWebhook", [2420, 180], {"respondWith": "json", "responseBody": f"={{\"ok\":false,\"workflow\":\"{name}\",\"error_id\":\"{{$json.error_id}}\"}}", "options": {"responseCode": 502}}),
    ]
    connections = {
        "Webhook": {"main": [[{"node": "Normalize Input", "type": "main", "index": 0}]]},
        "Normalize Input": {"main": [[{"node": "Check Secret", "type": "main", "index": 0}]]},
        "Check Secret": {"main": [[{"node": "Load Context", "type": "main", "index": 0}], [{"node": "Reject Unauthorized", "type": "main", "index": 0}]]},
        "Load Context": {"main": [[{"node": "Is Allowed?", "type": "main", "index": 0}]]},
        "Is Allowed?": {"main": [[{"node": "Is Dry Run?", "type": "main", "index": 0}], [{"node": "Reject Blocked", "type": "main", "index": 0}]]},
        "Is Dry Run?": {"main": [[{"node": "Build Dry Run Output", "type": "main", "index": 0}], [{"node": "Build Model Request", "type": "main", "index": 0}]]},
        "Build Dry Run Output": {"main": [[{"node": "Store Output", "type": "main", "index": 0}]]},
        "Build Model Request": {"main": [[{"node": "Call OpenAI or LiteLLM", "type": "main", "index": 0}]]},
        "Call OpenAI or LiteLLM": {"main": [[{"node": "Parse Model Response", "type": "main", "index": 0}]]},
        "Parse Model Response": {"main": [[{"node": "Model Call Failed?", "type": "main", "index": 0}]]},
        "Model Call Failed?": {"main": [[{"node": "Store Model Error", "type": "main", "index": 0}], [{"node": "Store Output", "type": "main", "index": 0}]]},
        "Store Output": {"main": [[{"node": "Respond Success", "type": "main", "index": 0}]]},
        "Store Model Error": {"main": [[{"node": "Respond Error", "type": "main", "index": 0}]]},
    }
    return {"name": name, "nodes": nodes, "connections": connections, "active": False, "settings": {}, "versionId": "v1.0-rc-pre-n8n-llm"}


def main() -> None:
    WORKFLOWS.mkdir(exist_ok=True)
    for name, args in CONFIG.items():
        output = workflow(name, *args)
        path = WORKFLOWS / f"{name}.json"
        path.write_text(json.dumps(output, indent=2) + "\n")
        print(f"generated {path}")


if __name__ == "__main__":
    main()
