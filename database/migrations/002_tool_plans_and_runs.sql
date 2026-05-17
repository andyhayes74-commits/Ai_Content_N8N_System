-- Non-breaking v2.2 tables for plan-driven orchestration and tool run tracking.

CREATE TABLE IF NOT EXISTS content_job_tool_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  source_output_id UUID REFERENCES content_outputs(id) ON DELETE SET NULL,
  plan_version INT NOT NULL DEFAULT 1,
  status TEXT NOT NULL DEFAULT 'active',
  selected_tools JSONB NOT NULL DEFAULT '[]'::jsonb,
  execution_order JSONB NOT NULL DEFAULT '[]'::jsonb,
  missing_inputs JSONB NOT NULL DEFAULT '[]'::jsonb,
  missing_capabilities JSONB NOT NULL DEFAULT '[]'::jsonb,
  approval_policy TEXT NOT NULL DEFAULT 'full_staged',
  plan_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_job_tool_runs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  plan_id UUID REFERENCES content_job_tool_plans(id) ON DELETE SET NULL,
  tool_id TEXT NOT NULL,
  workflow_name TEXT NOT NULL,
  step_number INT,
  status TEXT NOT NULL DEFAULT 'queued',
  input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT,
  failure_mode TEXT,
  retry_count INT NOT NULL DEFAULT 0,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_tool_plans_job_status ON content_job_tool_plans(job_id, status);
CREATE INDEX IF NOT EXISTS idx_tool_runs_job_status ON content_job_tool_runs(job_id, status);
