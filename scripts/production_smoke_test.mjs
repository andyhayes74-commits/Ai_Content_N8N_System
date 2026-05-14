#!/usr/bin/env node

const baseUrl = required('N8N_BASE_URL').replace(/\/+$/, '');
const webhookAuth = required('AI_AGENT_WEBHOOK_AUTH');
const apiKey = process.env.N8N_API_KEY || '';
const mode = process.env.AI_CONTENT_TEST_MODE || 'dry_run';
const prefix = process.env.AI_CONTENT_TEST_PREFIX || 'production-smoke';

function required(name) {
  const value = process.env[name];
  if (!value || !value.trim()) {
    throw new Error(`${name} is required.`);
  }
  return value.trim();
}

async function postWebhook(path, payload) {
  const response = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: {
      Authorization: webhookAuth.startsWith('Bearer ') ? webhookAuth : `Bearer ${webhookAuth}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  });
  const text = await response.text();
  let data;
  try {
    data = JSON.parse(text);
  } catch {
    data = { raw: text };
  }
  if (!response.ok) {
    throw new Error(`${path} failed with HTTP ${response.status}: ${text}`);
  }
  return data;
}

async function n8nApi(path) {
  if (!apiKey) {
    return null;
  }
  const response = await fetch(`${baseUrl}${path}`, {
    headers: {
      'X-N8N-API-KEY': apiKey,
      'Content-Type': 'application/json',
    },
  });
  const text = await response.text();
  if (!response.ok) {
    throw new Error(`n8n API ${path} failed with HTTP ${response.status}: ${text}`);
  }
  return JSON.parse(text);
}

function assert(condition, message) {
  if (!condition) {
    throw new Error(message);
  }
}

const externalJobRef = `${prefix}-${Date.now()}`;

const created = await postWebhook('/webhook/v1/orchestrator', {
  action: 'create_job',
  mode,
  external_job_ref: externalJobRef,
  project_name: 'Production smoke test',
  brief_text: 'Create a short dry-run content pack for production smoke testing.',
  drive_folder_id: 'dry-run-drive-folder',
  client_profile: {
    client_code: 'production_smoke_test',
    client_name: 'Production Smoke Test',
    default_approval_policy: 'qa_only',
    output_defaults: {
      requested_outputs: ['social_posts'],
    },
  },
});

assert(created.job_id, 'create_job did not return job_id');
assert(created.status === 'waiting_for_analysis_approval', `unexpected create_job status: ${created.status}`);

const planned = await postWebhook('/webhook/v1/orchestrator', {
  action: 'generate_plan',
  mode,
  job_id: created.job_id,
});

assert(planned.plan_id, 'generate_plan did not return plan_id');
assert(planned.tool_execution_plan?.approval_policy === 'qa_only', 'planner did not preserve qa_only policy');
assert(Array.isArray(planned.tool_execution_plan?.selected_tools), 'planner did not return selected_tools');

const completed = await postWebhook('/webhook/v1/orchestrator', {
  action: 'run_plan',
  mode,
  job_id: created.job_id,
});

assert(completed.status === 'delivery_ready', `run_plan did not reach delivery_ready: ${completed.status}`);

const status = await postWebhook('/webhook/v1/supervisor', {
  action: 'check_status',
  job_id: created.job_id,
});

assert(status.job_id || status.status || status.jobs, 'supervisor check_status returned no recognizable status payload');

const executions = await n8nApi('/api/v1/executions?limit=10');

console.log(JSON.stringify({
  ok: true,
  mode,
  job_id: created.job_id,
  plan_id: planned.plan_id,
  final_status: completed.status,
  recent_execution_statuses: executions?.data?.map((execution) => ({
    id: execution.id,
    workflowId: execution.workflowId,
    status: execution.status,
  })) ?? 'not_checked',
}, null, 2));
