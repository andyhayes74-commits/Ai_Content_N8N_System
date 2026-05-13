#!/usr/bin/env node

import { readdir, readFile } from 'node:fs/promises';
import { join, resolve } from 'node:path';

const ACTIVE_DIR = resolve('workflows/active');
const REQUIRED_FIELDS = ['name', 'nodes', 'connections', 'settings'];
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

function parseBool(value, defaultValue = false) {
  if (value === undefined || value === null || value === '') return defaultValue;
  const normalized = String(value).trim().toLowerCase();
  if (['1', 'true', 'yes', 'y', 'on'].includes(normalized)) return true;
  if (['0', 'false', 'no', 'n', 'off'].includes(normalized)) return false;
  throw new Error(`Invalid boolean value: ${value}`);
}

function requireEnv(name) {
  const value = process.env[name];
  if (!value || !value.trim()) throw new Error(`${name} is required when DRY_RUN=false.`);
  return value.trim();
}

function normalizeBaseUrl(value) {
  return value.replace(/\/+$/, '');
}

function redactSecrets(text, secrets) {
  let redacted = String(text ?? '');
  for (const secret of secrets) {
    if (secret) redacted = redacted.split(secret).join('[REDACTED]');
  }
  return redacted;
}

async function readActiveWorkflowFiles() {
  const entries = await readdir(ACTIVE_DIR, { withFileTypes: true });
  const files = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith('.json'))
    .map((entry) => join(ACTIVE_DIR, entry.name))
    .sort();
  if (files.length === 0) throw new Error(`No active workflow JSON files found in ${ACTIVE_DIR}.`);
  return files;
}

async function readWorkflow(filePath) {
  const raw = await readFile(filePath, 'utf8');
  const workflow = JSON.parse(raw);
  if (!workflow || typeof workflow !== 'object' || Array.isArray(workflow)) {
    throw new Error(`${filePath}: workflow JSON must contain one workflow object.`);
  }
  const missing = REQUIRED_FIELDS.filter((field) => {
    if (field === 'name') return typeof workflow.name !== 'string' || !workflow.name.trim();
    if (field === 'nodes') return !Array.isArray(workflow.nodes);
    return !workflow[field] || typeof workflow[field] !== 'object' || Array.isArray(workflow[field]);
  });
  if (missing.length > 0) throw new Error(`${filePath}: missing required deploy field(s): ${missing.join(', ')}`);
  return { filePath, workflow };
}

function sanitizeWorkflow(workflow) {
  return Object.fromEntries(REQUIRED_FIELDS.map((field) => [field, workflow[field]]));
}

function summarize({ filePath, workflow, dryRun, targetId, payload }) {
  const excludedPresent = EXCLUDED_UPDATE_FIELDS.filter((field) => Object.hasOwn(workflow, field));
  console.log('');
  console.log(`Mode: ${dryRun ? 'dry run (validate only)' : 'deploy'}`);
  console.log(`Workflow file: ${filePath}`);
  console.log(`Workflow name: ${workflow.name}`);
  console.log(`Node count: ${workflow.nodes.length}`);
  console.log(`Target n8n workflow ID: ${targetId || '[lookup by name / create if missing]'}`);
  console.log('Required fields:');
  for (const field of REQUIRED_FIELDS) console.log(`- ${field}: present`);
  console.log(`Read-only/excluded fields always removed from update payload when present: ${EXCLUDED_UPDATE_FIELDS.join(', ')}`);
  console.log(`Read-only/excluded fields removed from this workflow: ${excludedPresent.length ? excludedPresent.join(', ') : '[none present]'}`);
  console.log(`Update payload fields to send: ${Object.keys(payload).join(', ')}`);
}

async function n8nRequest({ baseUrl, apiKey, method, path, body }) {
  const response = await fetch(`${baseUrl}${path}`, {
    method,
    headers: { 'X-N8N-API-KEY': apiKey, 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const text = await response.text();
  let data = undefined;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }
  return { response, data, text };
}

function workflowList(data) {
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.data)) return data.data;
  if (Array.isArray(data?.workflows)) return data.workflows;
  return [];
}

async function fetchExistingWorkflows({ baseUrl, apiKey, secrets }) {
  const byName = new Map();
  let cursor = '';
  do {
    const query = cursor ? `?limit=100&cursor=${encodeURIComponent(cursor)}` : '?limit=100';
    const result = await n8nRequest({ baseUrl, apiKey, method: 'GET', path: `/api/v1/workflows${query}` });
    if (!result.response.ok) {
      throw new Error(`GET /api/v1/workflows failed with HTTP ${result.response.status}: ${redactSecrets(result.text, secrets)}`);
    }
    for (const workflow of workflowList(result.data)) {
      if (workflow?.name) byName.set(workflow.name, workflow);
    }
    cursor = result.data?.nextCursor || '';
  } while (cursor);
  return byName;
}

function requestError(method, path, result, secrets) {
  return `${method} ${path} failed with HTTP ${result.response.status} ${result.response.statusText}: ${redactSecrets(result.text || JSON.stringify(result.data ?? ''), secrets)}`;
}

async function updateWorkflow({ baseUrl, apiKey, workflowId, payload, secrets }) {
  const path = `/api/v1/workflows/${encodeURIComponent(workflowId)}`;
  const put = await n8nRequest({ baseUrl, apiKey, method: 'PUT', path, body: payload });
  if (put.response.ok) return { method: 'PUT', data: put.data };
  if (put.response.status !== 405) throw new Error(requestError('PUT', path, put, secrets));
  console.log('PUT update returned HTTP 405; retrying once with PATCH.');
  const patch = await n8nRequest({ baseUrl, apiKey, method: 'PATCH', path, body: payload });
  if (!patch.response.ok) throw new Error(`${requestError('PUT', path, put, secrets)}\n${requestError('PATCH', path, patch, secrets)}`);
  return { method: 'PATCH', data: patch.data };
}

async function createWorkflow({ baseUrl, apiKey, payload, secrets }) {
  const path = '/api/v1/workflows';
  const result = await n8nRequest({ baseUrl, apiKey, method: 'POST', path, body: payload });
  if (!result.response.ok) throw new Error(requestError('POST', path, result, secrets));
  return result.data;
}

async function setActivation({ baseUrl, apiKey, workflowId, active, secrets }) {
  const path = `/api/v1/workflows/${encodeURIComponent(workflowId)}/${active ? 'activate' : 'deactivate'}`;
  const result = await n8nRequest({ baseUrl, apiKey, method: 'POST', path });
  if (!result.response.ok) throw new Error(requestError('POST', path, result, secrets));
}

function returnedId(data, fallback) {
  return data?.data?.id ?? data?.id ?? fallback;
}

async function main() {
  const dryRun = parseBool(process.env.DRY_RUN, true);
  const activeOverride = process.env.N8N_DEPLOY_ACTIVE === undefined || process.env.N8N_DEPLOY_ACTIVE === ''
    ? undefined
    : parseBool(process.env.N8N_DEPLOY_ACTIVE);

  const workflows = [];
  const names = new Set();
  for (const filePath of await readActiveWorkflowFiles()) {
    const item = await readWorkflow(filePath);
    if (names.has(item.workflow.name)) throw new Error(`Duplicate active workflow name: ${item.workflow.name}`);
    names.add(item.workflow.name);
    workflows.push({ ...item, payload: sanitizeWorkflow(item.workflow) });
  }

  console.log(`Active workflow count: ${workflows.length}`);
  console.log(`Active workflow names: ${workflows.map((item) => item.workflow.name).join(', ')}`);

  let baseUrl = '';
  let apiKey = '';
  let secrets = [];
  let existingByName = new Map();
  if (!dryRun) {
    baseUrl = normalizeBaseUrl(requireEnv('N8N_BASE_URL'));
    apiKey = requireEnv('N8N_API_KEY');
    secrets = [apiKey];
    existingByName = await fetchExistingWorkflows({ baseUrl, apiKey, secrets });
    console.log(`Existing n8n workflows visible to API: ${existingByName.size}`);
  }

  const summary = [];
  for (const item of workflows) {
    const existing = existingByName.get(item.workflow.name);
    summarize({ filePath: item.filePath, workflow: item.workflow, dryRun, targetId: existing?.id, payload: item.payload });

    if (dryRun) {
      summary.push({ name: item.workflow.name, action: 'validated' });
      continue;
    }

    let action;
    let data;
    if (existing?.id) {
      const result = await updateWorkflow({ baseUrl, apiKey, workflowId: existing.id, payload: item.payload, secrets });
      data = result.data;
      action = `updated via ${result.method}`;
    } else {
      data = await createWorkflow({ baseUrl, apiKey, payload: item.payload, secrets });
      action = 'created';
    }

    const id = returnedId(data, existing?.id);
    console.log(`Workflow ${action}: ${id} / ${item.workflow.name}`);

    if (activeOverride !== undefined && id) {
      await setActivation({ baseUrl, apiKey, workflowId: id, active: activeOverride, secrets });
      console.log(`Workflow ${activeOverride ? 'activation' : 'deactivation'} succeeded for ${id}.`);
    }

    summary.push({ name: item.workflow.name, action, id });
  }

  console.log('');
  console.log('Deployment summary:');
  for (const item of summary) console.log(`- ${item.name}: ${item.action}${item.id ? ` (${item.id})` : ''}`);
  if (dryRun) console.log('Dry run complete. No n8n API calls were made.');
}

main().catch((error) => {
  console.error(redactSecrets(error.stack || error.message, [process.env.N8N_API_KEY]));
  process.exit(1);
});
