#!/usr/bin/env python3
"""Generate Google Drive-ready workflows for the AI Content n8n System.

These workflows use HTTP Request nodes targeting the Google Drive REST API so they
are import-shape ready without committing OAuth credentials. In n8n, attach an
OAuth2/Google credential to the HTTP Request nodes or replace them with native
Google Drive nodes during sandbox hardening.
"""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"


def node(id_, name, type_, pos, params, version=1):
    return {"id": str(id_), "name": name, "type": type_, "typeVersion": version, "position": pos, "parameters": params}


def common_start(name):
    return [
        node(1, "Webhook", "n8n-nodes-base.webhook", [0, 0], {"path": f"v1/{name}", "httpMethod": "POST", "responseMode": "responseNode"}),
        node(2, "Normalize Input", "n8n-nodes-base.code", [220, 0], {"jsCode": "const body=$json.body??$json;const headers=$json.headers??{};const rawJobId=String(body.job_id||$json.job_id||'');const jobId=/^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$/.test(rawJobId)?rawJobId:'';return [{json:{...body,job_id:jobId,mode:body.mode||'live',agent_secret:headers['x-agent-secret']||headers['X-Agent-Secret']||''}}];"}, 2),
        node(3, "Check Secret", "n8n-nodes-base.if", [440, 0], {"conditions": {"string": [{"value1": "={{$json.agent_secret}}", "operation": "equal", "value2": "={{$env.AGENT_WEBHOOK_SECRET}}"}]}}),
        node(4, "Reject Unauthorized", "n8n-nodes-base.respondToWebhook", [660, -180], {"respondWith": "json", "responseBody": "={\"ok\":false,\"error\":\"unauthorized\"}", "options": {"responseCode": 401}}),
    ]


def common_connections(first_after_secret):
    return {
        "Webhook": {"main": [[{"node": "Normalize Input", "type": "main", "index": 0}]]},
        "Normalize Input": {"main": [[{"node": "Check Secret", "type": "main", "index": 0}]]},
        "Check Secret": {"main": [[{"node": first_after_secret, "type": "main", "index": 0}], [{"node": "Reject Unauthorized", "type": "main", "index": 0}]]},
    }


def create_new_drive_project_folder():
    name = "create_new_drive_project_folder"
    nodes = common_start(name) + [
        node(5, "Load Job", "n8n-nodes-base.postgres", [660, 0], {"operation": "executeQuery", "query": "=SELECT j.id::text AS job_id, regexp_replace(COALESCE(c.client_name,'Client') || '_' || j.project_name || '_' || to_char(now(),'YYYY-MM-DD'),'[^A-Za-z0-9_-]+','_','g') AS folder_name FROM content_jobs j LEFT JOIN client_profiles c ON c.id=j.client_profile_id WHERE j.id=NULLIF('{{$json.job_id}}','')::uuid;"}),
        node(6, "Build Drive Folder Request", "n8n-nodes-base.code", [880, 0], {"jsCode": "return [{json:{...$json,drive_request:{name:$json.folder_name,mimeType:'application/vnd.google-apps.folder',parents:[$env.DEFAULT_PARENT_DRIVE_FOLDER_ID]},credential_marker:'GOOGLE_DRIVE_AI_CONTENT'}}];"}, 2),
        node(7, "Create Folder in Google Drive", "n8n-nodes-base.httpRequest", [1100, 0], {"method": "POST", "url": "https://www.googleapis.com/drive/v3/files", "sendHeaders": True, "headerParameters": {"parameters": [{"name": "Authorization", "value": "={{'Bearer ' + $env.GOOGLE_DRIVE_ACCESS_TOKEN}}"}, {"name": "Content-Type", "value": "application/json"}]}, "sendBody": True, "specifyBody": "json", "jsonBody": "={{JSON.stringify($json.drive_request)}}", "options": {"timeout": 120000}}, 4),
        node(8, "Register Drive Folder", "n8n-nodes-base.postgres", [1320, 0], {"operation": "executeQuery", "query": "=WITH update_job AS (UPDATE content_jobs SET drive_root_folder_id=COALESCE(NULLIF('{{$json.id || $json.drive_folder_id || \"\"}}',''),'PENDING_GOOGLE_DRIVE_CREATION'), drive_root_folder_path='{{$node[\"Load Job\"].json.folder_name}}', updated_at=now() WHERE id=NULLIF('{{$node[\"Load Job\"].json.job_id}}','')::uuid RETURNING id,drive_root_folder_id), event_insert AS (INSERT INTO content_events (job_id,event_type,message,metadata) SELECT id,'drive_project_folder_created','Project Drive folder created or prepared',jsonb_build_object('drive_root_folder_id',drive_root_folder_id,'credential','GOOGLE_DRIVE_AI_CONTENT') FROM update_job) SELECT id::text AS job_id, drive_root_folder_id FROM update_job;"}),
        node(9, "Respond", "n8n-nodes-base.respondToWebhook", [1540, 0], {"respondWith": "json", "responseBody": "={{$json}}", "options": {"responseCode": 200}}),
    ]
    con = common_connections("Load Job")
    con.update({"Load Job": {"main": [[{"node": "Build Drive Folder Request", "type": "main", "index": 0}]]}, "Build Drive Folder Request": {"main": [[{"node": "Create Folder in Google Drive", "type": "main", "index": 0}]]}, "Create Folder in Google Drive": {"main": [[{"node": "Register Drive Folder", "type": "main", "index": 0}]]}, "Register Drive Folder": {"main": [[{"node": "Respond", "type": "main", "index": 0}]]}})
    return {"name": name, "nodes": nodes, "connections": con, "active": False, "settings": {}, "versionId": "v1.0-rc-pre-n8n-drive"}


def create_standard_folder_structure():
    name="create_standard_folder_structure"
    folders=["00_Admin","01_Input","02_Parsed","03_Strategy","04_Copy","05_Images","06_Video","07_Delivery"]
    nodes=common_start(name)+[
        node(5,"Load Job","n8n-nodes-base.postgres",[660,0],{"operation":"executeQuery","query":"=SELECT id::text AS job_id, drive_root_folder_id FROM content_jobs WHERE id=NULLIF('{{$json.job_id}}','')::uuid;"}),
        node(6,"Build Folder Batch","n8n-nodes-base.code",[880,0],{"jsCode":f"const folders={json.dumps(folders)};return folders.map(name=>({{json:{{job_id:$json.job_id,parent_folder_id:$json.drive_root_folder_id,folder_name:name,drive_request:{{name,mimeType:'application/vnd.google-apps.folder',parents:[$json.drive_root_folder_id]}},credential_marker:'GOOGLE_DRIVE_AI_CONTENT'}}}}));"},2),
        node(7,"Create Subfolder in Google Drive","n8n-nodes-base.httpRequest",[1100,0],{"method":"POST","url":"https://www.googleapis.com/drive/v3/files","sendHeaders":True,"headerParameters":{"parameters":[{"name":"Authorization","value":"={{'Bearer ' + $env.GOOGLE_DRIVE_ACCESS_TOKEN}}"},{"name":"Content-Type","value":"application/json"}]},"sendBody":True,"specifyBody":"json","jsonBody":"={{JSON.stringify($json.drive_request)}}","options":{"timeout":120000}},4),
        node(8,"Record Folder Structure","n8n-nodes-base.postgres",[1320,0],{"operation":"executeQuery","query":"=WITH event_insert AS (INSERT INTO content_events (job_id,event_type,message,metadata) VALUES (NULLIF('{{$json.job_id}}','')::uuid,'drive_standard_folder_created','Standard Drive subfolder created or prepared',jsonb_build_object('folder_name','{{$json.folder_name}}','drive_folder_id','{{$json.id || \"PENDING_GOOGLE_DRIVE_CREATION\"}}','credential','GOOGLE_DRIVE_AI_CONTENT')) RETURNING id) SELECT id::text AS event_id;"}),
        node(9,"Respond","n8n-nodes-base.respondToWebhook",[1540,0],{"respondWith":"json","responseBody":"={\"ok\":true,\"workflow\":\"create_standard_folder_structure\",\"mode\":\"per-folder events recorded\"}","options":{"responseCode":200}}),
    ]
    con=common_connections("Load Job")
    con.update({"Load Job":{"main":[[{"node":"Build Folder Batch","type":"main","index":0}]]},"Build Folder Batch":{"main":[[{"node":"Create Subfolder in Google Drive","type":"main","index":0}]]},"Create Subfolder in Google Drive":{"main":[[{"node":"Record Folder Structure","type":"main","index":0}]]},"Record Folder Structure":{"main":[[{"node":"Respond","type":"main","index":0}]]}})
    return {"name":name,"nodes":nodes,"connections":con,"active":False,"settings":{},"versionId":"v1.0-rc-pre-n8n-drive"}


def scan_drive_assets():
    name="scan_drive_assets"
    nodes=common_start(name)+[
        node(5,"Load Job","n8n-nodes-base.postgres",[660,0],{"operation":"executeQuery","query":"=SELECT id::text AS job_id, drive_root_folder_id FROM content_jobs WHERE id=NULLIF('{{$json.job_id}}','')::uuid;"}),
        node(6,"List Drive Files","n8n-nodes-base.httpRequest",[880,0],{"method":"GET","url":"={{'https://www.googleapis.com/drive/v3/files?q=' + encodeURIComponent('\'' + $json.drive_root_folder_id + '\'' + ' in parents and trashed=false') + '&fields=files(id,name,mimeType,size)'}}","sendHeaders":True,"headerParameters":{"parameters":[{"name":"Authorization","value":"={{'Bearer ' + $env.GOOGLE_DRIVE_ACCESS_TOKEN}}"}]},"options":{"timeout":120000}},4),
        node(7,"Build Asset Rows","n8n-nodes-base.code",[1100,0],{"jsCode":"const jobId=$node['Load Job'].json.job_id;const files=$json.files||[];return files.map(f=>({json:{job_id:jobId,drive_file_id:f.id,file_name:String(f.name||'unnamed').replace(/'/g,\"''\"),mime_type:f.mimeType||'',file_size_bytes:f.size||null,source_type:'drive_file'}}));"},2),
        node(8,"Register Asset","n8n-nodes-base.postgres",[1320,0],{"operation":"executeQuery","query":"=WITH inserted AS (INSERT INTO content_assets (job_id,source_type,drive_file_id,file_name,mime_type,file_size_bytes,parse_status,extracted_metadata) VALUES (NULLIF('{{$json.job_id}}','')::uuid,'{{$json.source_type}}','{{$json.drive_file_id}}','{{$json.file_name}}','{{$json.mime_type}}',NULLIF('{{$json.file_size_bytes || \"\"}}','')::bigint,'queued',jsonb_build_object('source','google_drive_list','credential','GOOGLE_DRIVE_AI_CONTENT')) RETURNING id,job_id), event_insert AS (INSERT INTO content_events (job_id,event_type,message,metadata) SELECT job_id,'drive_asset_registered','Drive asset registered',jsonb_build_object('asset_id',id) FROM inserted) SELECT id::text AS asset_id FROM inserted;"}),
        node(9,"Respond","n8n-nodes-base.respondToWebhook",[1540,0],{"respondWith":"json","responseBody":"={\"ok\":true,\"workflow\":\"scan_drive_assets\",\"asset_id\":\"{{$json.asset_id || ''}}\"}","options":{"responseCode":200}}),
    ]
    con=common_connections("Load Job")
    con.update({"Load Job":{"main":[[{"node":"List Drive Files","type":"main","index":0}]]},"List Drive Files":{"main":[[{"node":"Build Asset Rows","type":"main","index":0}]]},"Build Asset Rows":{"main":[[{"node":"Register Asset","type":"main","index":0}]]},"Register Asset":{"main":[[{"node":"Respond","type":"main","index":0}]]}})
    return {"name":name,"nodes":nodes,"connections":con,"active":False,"settings":{},"versionId":"v1.0-rc-pre-n8n-drive"}


def simple_http_marker_workflow(name, event_type, message, output=False):
    nodes=common_start(name)+[
        node(5,"Load Job","n8n-nodes-base.postgres",[660,0],{"operation":"executeQuery","query":"=SELECT id::text AS job_id, drive_root_folder_id FROM content_jobs WHERE id=NULLIF('{{$json.job_id}}','')::uuid;"}),
        node(6,"Google Drive API Placeholder","n8n-nodes-base.httpRequest",[880,0],{"method":"GET","url":"https://www.googleapis.com/drive/v3/files","sendHeaders":True,"headerParameters":{"parameters":[{"name":"Authorization","value":"={{'Bearer ' + $env.GOOGLE_DRIVE_ACCESS_TOKEN}}"}]},"options":{"timeout":120000}},4),
        node(7,"Record Drive Step","n8n-nodes-base.postgres",[1100,0],{"operation":"executeQuery","query":f"=WITH event_insert AS (INSERT INTO content_events (job_id,event_type,message,metadata) VALUES (NULLIF('{{$node[\"Load Job\"].json.job_id}}','')::uuid,'{event_type}','{message}',jsonb_build_object('credential','GOOGLE_DRIVE_AI_CONTENT','drive_node_present',true)) RETURNING id), output_insert AS (INSERT INTO content_outputs (job_id, output_type, title, structured_data, qa_status) SELECT NULLIF('{{$node[\"Load Job\"].json.job_id}}','')::uuid,'asset_index','Asset Index',COALESCE((SELECT jsonb_agg(jsonb_build_object('file_name',file_name,'mime_type',mime_type,'parse_status',parse_status)) FROM content_assets WHERE job_id=NULLIF('{{$node[\"Load Job\"].json.job_id}}','')::uuid),'[]'::jsonb),'pending' WHERE '{str(output).lower()}'='true' RETURNING id) SELECT (SELECT id::text FROM event_insert) AS event_id,(SELECT id::text FROM output_insert) AS output_id;"}),
        node(8,"Respond","n8n-nodes-base.respondToWebhook",[1320,0],{"respondWith":"json","responseBody":f"={{\"ok\":true,\"workflow\":\"{name}\",\"event_id\":\"{{$json.event_id}}\",\"output_id\":\"{{$json.output_id || ''}}\"}}","options":{"responseCode":200}}),
    ]
    con=common_connections("Load Job")
    con.update({"Load Job":{"main":[[{"node":"Google Drive API Placeholder","type":"main","index":0}]]},"Google Drive API Placeholder":{"main":[[{"node":"Record Drive Step","type":"main","index":0}]]},"Record Drive Step":{"main":[[{"node":"Respond","type":"main","index":0}]]}})
    return {"name":name,"nodes":nodes,"connections":con,"active":False,"settings":{},"versionId":"v1.0-rc-pre-n8n-drive"}


def generate_delivery_pack():
    name="generate_delivery_pack"
    nodes=common_start(name)+[
        node(5,"Check Final Approval","n8n-nodes-base.postgres",[660,0],{"operation":"executeQuery","query":"=WITH gate AS (SELECT EXISTS (SELECT 1 FROM content_approvals WHERE job_id=NULLIF('{{$json.job_id}}','')::uuid AND approval_stage='final_delivery' AND decision='approved') AS allowed), outputs AS (SELECT COALESCE(jsonb_agg(jsonb_build_object('output_type',output_type,'title',title,'qa_status',qa_status,'structured_data',structured_data)),'[]'::jsonb) AS package_data FROM content_outputs WHERE job_id=NULLIF('{{$json.job_id}}','')::uuid) SELECT (SELECT allowed FROM gate) AS allowed, NULLIF('{{$json.job_id}}','') AS job_id, (SELECT package_data::text FROM outputs) AS package_json;"}),
        node(6,"Is Approved?","n8n-nodes-base.if",[880,0],{"conditions":{"boolean":[{"value1":"={{$json.allowed}}","operation":"equal","value2":True}]}}),
        node(7,"Reject Missing Approval","n8n-nodes-base.respondToWebhook",[1100,-180],{"respondWith":"json","responseBody":"={\"ok\":false,\"error\":\"final_delivery_approval_required\"}","options":{"responseCode":409}}),
        node(8,"Upload Delivery Metadata to Drive","n8n-nodes-base.httpRequest",[1100,80],{"method":"POST","url":"https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart","sendHeaders":True,"headerParameters":{"parameters":[{"name":"Authorization","value":"={{'Bearer ' + $env.GOOGLE_DRIVE_ACCESS_TOKEN}}"}]},"sendBody":True,"bodyParameters":{"parameters":[{"name":"metadata","value":"={{JSON.stringify({name:'delivery_pack.json',mimeType:'application/json'})}}"},{"name":"file","value":"={{$json.package_json}}"}]},"options":{"timeout":120000}},4),
        node(9,"Store Delivery Pack","n8n-nodes-base.postgres",[1320,80],{"operation":"executeQuery","query":"=WITH output_summary AS (SELECT COALESCE(jsonb_agg(jsonb_build_object('type',output_type,'title',title,'qa_status',qa_status,'id',id)),'[]'::jsonb) AS outputs FROM content_outputs WHERE job_id=NULLIF('{{$node[\"Check Final Approval\"].json.job_id}}','')::uuid), pack_insert AS (INSERT INTO content_outputs (job_id,output_type,title,structured_data,qa_status,drive_file_id) SELECT NULLIF('{{$node[\"Check Final Approval\"].json.job_id}}','')::uuid,'delivery_pack','Delivery Pack',jsonb_build_object('included_outputs',(SELECT outputs FROM output_summary),'drive_upload_response','{{$json.id || \"PENDING_GOOGLE_DRIVE_UPLOAD\"}}'),'passed','{{$json.id || \"\"}}' RETURNING id), job_update AS (UPDATE content_jobs SET status='delivery_ready',updated_at=now() WHERE id=NULLIF('{{$node[\"Check Final Approval\"].json.job_id}}','')::uuid RETURNING id), event_insert AS (INSERT INTO content_events (job_id,event_type,message,metadata) SELECT NULLIF('{{$node[\"Check Final Approval\"].json.job_id}}','')::uuid,'delivery_pack_ready','Delivery pack created and ready for human delivery',jsonb_build_object('delivery_pack_id',(SELECT id FROM pack_insert),'credential','GOOGLE_DRIVE_AI_CONTENT')) SELECT (SELECT id::text FROM pack_insert) AS delivery_pack_id;"}),
        node(10,"Respond","n8n-nodes-base.respondToWebhook",[1540,80],{"respondWith":"json","responseBody":"={\"ok\":true,\"workflow\":\"generate_delivery_pack\",\"delivery_pack_id\":\"{{$json.delivery_pack_id}}\"}","options":{"responseCode":200}}),
    ]
    con=common_connections("Check Final Approval")
    con.update({"Check Final Approval":{"main":[[{"node":"Is Approved?","type":"main","index":0}]]},"Is Approved?":{"main":[[{"node":"Upload Delivery Metadata to Drive","type":"main","index":0}],[{"node":"Reject Missing Approval","type":"main","index":0}]]},"Upload Delivery Metadata to Drive":{"main":[[{"node":"Store Delivery Pack","type":"main","index":0}]]},"Store Delivery Pack":{"main":[[{"node":"Respond","type":"main","index":0}]]}})
    return {"name":name,"nodes":nodes,"connections":con,"active":False,"settings":{},"versionId":"v1.0-rc-pre-n8n-drive"}


def main():
    builders=[create_new_drive_project_folder,create_standard_folder_structure,scan_drive_assets,
        lambda: simple_http_marker_workflow('parse_and_summarise_documents','documents_parse_drive_step','Document parsing Drive step prepared'),
        lambda: simple_http_marker_workflow('create_asset_index','asset_index_created','Asset index created with Drive step present',True),
        generate_delivery_pack]
    WORKFLOWS.mkdir(exist_ok=True)
    for build in builders:
        wf=build(); (WORKFLOWS/f"{wf['name']}.json").write_text(json.dumps(wf,indent=2)+"\n"); print(f"generated workflows/{wf['name']}.json")
if __name__=='__main__': main()
