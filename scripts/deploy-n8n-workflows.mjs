#!/usr/bin/env node

import { readFile, readdir } from 'node:fs/promises';
import { resolve, join } from 'node:path';

const WORKFLOW_DIR = resolve('workflows/active');
const REQUIRED_FIELDS = ['name', 'nodes', 'connections', 'settings'];
const REQUIRED_WORKFLOWS = [
  'ai_content_orchestrator',
  'tool_job_intake',
  'tool_drive_assets',
  'tool_request_analysis',
  'tool_content_planning',
  'tool_content_generation',
  'tool_qa_delivery',
  'tool_logging',
  'api_supervisor_gateway',
  'api_human_review_gateway',
];
const EXCLUDED_UPDATE_FIELDS = [
  'id',
  'versionId',
  'active',
  'meta',
  'createdAt',
  'updatedAt',
  'triggerCount',
  'shared',
  'ownedBy',
  'homeProject',
  'usedCredentials',
  'tags',
  'pinData',
  'staticData',
];
const SECRET_PATTERNS = [
  /sk-[A-Za-z0-9]{20,}/,
  /AIza[0-9A-Za-z_-]{20,}/,
  /xox[baprs]-/,
];

function parseBool(value, defaultValue = false) {
  if (value === undefined || value === null || value === '') {
    return defaultValue;
  }
  const normalized = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes', 'y', 'on'].includes(normalized)) {
    return true;
  }
  if (['0', 'false', 'no', 'n', 'off'].includes(normalized)) {
    return false;
  }
  throw new Error(`Invalid boolean value: ${value}`);
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value || !value.trim()) {
    throw new Error(`${name} is required when DRY_RUN=false.`);
  }
  return value.trim();
}

function normalizeBaseUrl(value) {
  return value.replace(/\/+$/, '');
}

function envKeyForWorkflow(name) {
  return `N8N_WORKFLOW_ID_${name.toUpperCase().replace(/[^A-Z0-9]+/g, '_')}`;
}

function redactSecrets(text, secrets) {
  let redacted = text;
  for (const secret of secrets) {
    if (secret) {
      redacted = redacted.split(secret).join('[REDACTED]');
    }
  }
  return redacted;
}

function parseWorkflowIdMap() {
  const raw = process.env.N8N_WORKFLOW_ID_MAP?.trim();
  if (!raw) {
    return {};
  }
  try {
    const parsed = JSON.parse(raw);
    if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) {
      throw new Error('mapping must be a JSON object');
    }
    return parsed;
  } catch (error) {
    throw new Error(`N8N_WORKFLOW_ID_MAP must be valid JSON mapping workflow names to n8n IDs: ${error.message}`);
  }
}

function getWorkflowId(name, workflowIdMap) {
  return String(workflowIdMap[name] || process.env[envKeyForWorkflow(name)] || '').trim();
}

async function readWorkflowFile(path) {
  const raw = await readFile(path, 'utf8');
  return { raw, workflow: JSON.parse(raw), path };
}

function validateWorkflow(raw, workflow, path) {
  if (!workflow || typeof workflow !== 'object' || Array.isArray(workflow)) {
    throw new Error(`${path} must contain a single workflow object.`);
  }
  if (typeof workflow.name !== 'string' || !workflow.name.trim()) {
    throw new Error(`${path} is missing workflow.name.`);
  }
  if (!Array.isArray(workflow.nodes)) {
    throw new Error(`${workflow.name} is missing nodes array.`);
  }
  if (!workflow.connections || typeof workflow.connections !== 'object' || Array.isArray(workflow.connections)) {
    throw new Error(`${workflow.name} is missing connections object.`);
  }
  if (!workflow.settings || typeof workflow.settings !== 'object' || Array.isArray(workflow.settings)) {
    throw new Error(`${workflow.name} is missing settings object.`);
  }
  if (raw.includes('$env')) {
    throw new Error(`${workflow.name} still references environment variables. Use n8n credentials or payload fields.`);
  }
  if (raw.includes('{{{') || raw.includes('}}}')) {
    throw new Error(`${workflow.name} contains malformed triple-brace expression syntax.`);
  }
  for (const pattern of SECRET_PATTERNS) {
    if (pattern.test(raw)) {
      throw new Error(`${workflow.name} appears to contain a hardcoded secret.`);
    }
  }
}

function sanitizeWorkflow(workflow) {
  const sanitized = {};
  for (const field of REQUIRED_FIELDS) {
    sanitized[field] = workflow[field];
  }
  return sanitized;
}

async function readWorkflows() {
  const entries = await readdir(WORKFLOW_DIR, { withFileTypes: true });
  const paths = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
    .map((entry) => join(WORKFLOW_DIR, entry.name))
    .sort();

  const workflows = [];
  for (const path of paths) {
    const item = await readWorkflowFile(path);
    validateWorkflow(item.raw, item.workflow, path);
    workflows.push(item);
  }

  const names = workflows.map(({ workflow }) => workflow.name);
  const missing = REQUIRED_WORKFLOWS.filter((name) => !names.includes(name));
  const unexpected = names.filter((name) => !REQUIRED_WORKFLOWS.includes(name));
  if (missing.length > 0) {
    throw new Error(`Missing required workflow(s): ${missing.join(', ')}`);
  }
  if (unexpected.length > 0) {
    throw new Error(`Unexpected active workflow(s): ${unexpected.join(', ')}`);
  }

  return workflows.sort((a, b) => REQUIRED_WORKFLOWS.indexOf(a.workflow.name) - REQUIRED_WORKFLOWS.indexOf(b.workflow.name));
}

function summarizeWorkflow({ workflow, path }, workflowId, payload) {
  const excludedPresent = EXCLUDED_UPDATE_FIELDS.filter((field) => Object.prototype.hasOwnProperty.call(workflow, field));
  console.log(`- ${workflow.name}`);
  console.log(`  file: ${path}`);
  console.log(`  nodes: ${workflow.nodes.length}`);
  console.log(`  target n8n workflow ID: ${workflowId || '[not set]'}`);
  console.log(`  update payload fields: ${Object.keys(payload).join(', ')}`);
  console.log(`  excluded fields present: ${excludedPresent.length ? excludedPresent.join(', ') : '[none]'}`);
}

async function apiRequest({ baseUrl, workflowId, apiKey, method, path = '', body }) {
  const url = `${baseUrl}/api/v1/workflows/${encodeURIComponent(workflowId)}${path}`;
  const response = await fetch(url, {
    method,
    headers: {
      'X-N8N-API-KEY': apiKey,
      'Content-Type': 'application/json',
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let data = undefined;
  if (text) {
    try {
      data = JSON.parse(text);
    } catch {
      data = text;
    }
  }
  return { response, data, text };
}

async function checkedRequest(options, secrets) {
  const result = await apiRequest(options);
  if (!result.response.ok) {
    const body = result.text || JSON.stringify(result.data ?? '');
    throw new Error(
      `${options.method} ${options.path || ''} failed with HTTP ${result.response.status} ${result.response.statusText}: ${redactSecrets(body, secrets)}`,
    );
  }
  return result.data;
}

function formatFailedRequest(method, result, secrets) {
  return `${method} update failed with HTTP ${result.response.status} ${result.response.statusText}: ${redactSecrets(
    result.text || JSON.stringify(result.data ?? ''),
    secrets,
  )}`;
}

async function updateWorkflowWithFallback({ baseUrl, workflowId, apiKey, payload, secrets }) {
  const firstMethod = 'PUT';
  const fallbackMethod = 'PATCH';
  const first = await apiRequest({ baseUrl, workflowId, apiKey, method: firstMethod, body: payload });
  if (first.response.ok) {
    return { method: firstMethod, data: first.data };
  }
  const firstError = formatFailedRequest(firstMethod, first, secrets);
  if (first.response.status !== 405) {
    throw new Error(firstError);
  }
  console.log(`${firstMethod} returned HTTP 405 for ${workflowId}; retrying with ${fallbackMethod}.`);
  const fallback = await apiRequest({ baseUrl, workflowId, apiKey, method: fallbackMethod, body: payload });
  if (!fallback.response.ok) {
    throw new Error(`${firstError}\n${formatFailedRequest(fallbackMethod, fallback, secrets)}`);
  }
  return { method: fallbackMethod, data: fallback.data };
}

async function setActivation({ baseUrl, workflowId, apiKey, active, secrets }) {
  const endpoint = active ? '/activate' : '/deactivate';
  await checkedRequest({ baseUrl, workflowId, apiKey, method: 'POST', path: endpoint }, secrets);
}

async function main() {
  const dryRun = parseBool(process.env.DRY_RUN, true);
  const activeEnvProvided = process.env.N8N_DEPLOY_ACTIVE !== undefined && process.env.N8N_DEPLOY_ACTIVE !== '';
  const activeOverride = activeEnvProvided ? parseBool(process.env.N8N_DEPLOY_ACTIVE) : undefined;
  const workflowIdMap = parseWorkflowIdMap();
  const workflows = await readWorkflows();

  console.log(`Mode: ${dryRun ? 'dry run (validate only)' : 'deploy'}`);
  console.log(`Workflow directory: ${WORKFLOW_DIR}`);
  console.log(`Workflow count: ${workflows.length}`);

  const prepared = workflows.map((item) => ({
    item,
    workflowId: getWorkflowId(item.workflow.name, workflowIdMap),
    payload: sanitizeWorkflow(item.workflow),
  }));

  for (const preparedWorkflow of prepared) {
    summarizeWorkflow(preparedWorkflow.item, preparedWorkflow.workflowId, preparedWorkflow.payload);
  }

  if (dryRun) {
    console.log('Dry run complete. No n8n API calls were made.');
    return;
  }

  const missingIds = prepared
    .filter(({ workflowId }) => !workflowId)
    .map(({ item }) => `${item.workflow.name} (${envKeyForWorkflow(item.workflow.name)})`);
  if (missingIds.length > 0) {
    throw new Error(
      `Missing n8n workflow ID mapping for: ${missingIds.join(', ')}. Set N8N_WORKFLOW_ID_MAP or individual workflow ID secrets.`,
    );
  }

  const baseUrl = normalizeBaseUrl(requireEnv('N8N_BASE_URL'));
  const apiKey = requireEnv('N8N_API_KEY');
  const secrets = [apiKey];

  for (const { item, workflowId, payload } of prepared) {
    const name = item.workflow.name;
    let existingWorkflow;
    try {
      existingWorkflow = await checkedRequest({ baseUrl, workflowId, apiKey, method: 'GET' }, secrets);
      const existingName = existingWorkflow?.data?.name ?? existingWorkflow?.name;
      if (existingName && existingName !== name) {
        throw new Error(`target ID ${workflowId} is named ${existingName}, not ${name}`);
      }
    } catch (error) {
      throw new Error(`Pre-update check failed for ${name}: ${redactSecrets(error.message, secrets)}`);
    }

    const { method, data } = await updateWorkflowWithFallback({ baseUrl, workflowId, apiKey, payload, secrets });
    const updatedWorkflow = data?.data ?? data;
    console.log(`Updated ${name} via ${method}: ${updatedWorkflow?.id ?? workflowId}`);

    if (activeOverride !== undefined) {
      const updatedActive = updatedWorkflow?.active;
      if (updatedActive !== activeOverride) {
        await setActivation({ baseUrl, workflowId, apiKey, active: activeOverride, secrets });
        console.log(`${activeOverride ? 'Activated' : 'Deactivated'} ${name}.`);
      }
    }
  }

  console.log(`Deployment complete. Updated ${prepared.length} workflows.`);
}

main().catch((error) => {
  console.error(redactSecrets(error.stack || error.message, [process.env.N8N_API_KEY]));
  process.exit(1);
});
