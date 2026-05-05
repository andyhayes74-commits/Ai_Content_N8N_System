-- AI Content n8n System v1.0 RC schema

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

DO $$
BEGIN
  IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'job_status') THEN
    CREATE TYPE job_status AS ENUM (
      'created','intake_complete','assets_scanning','assets_parsed','analysis_complete',
      'waiting_for_analysis_approval','waiting_for_plan_approval','generating_outputs',
      'qa_in_progress','waiting_for_human_review','delivery_ready','completed','failed','paused','cancelled'
    );
  END IF;
END$$;

CREATE TABLE IF NOT EXISTS client_profiles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_code TEXT UNIQUE NOT NULL,
  client_name TEXT NOT NULL,
  preferred_tone TEXT,
  industry TEXT,
  compliance_notes TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_jobs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  external_job_ref TEXT UNIQUE,
  client_profile_id UUID REFERENCES client_profiles(id),
  project_name TEXT NOT NULL,
  brief_text TEXT NOT NULL,
  drive_root_folder_id TEXT,
  drive_root_folder_path TEXT,
  requested_outputs JSONB NOT NULL DEFAULT '[]'::jsonb,
  status job_status NOT NULL DEFAULT 'created',
  human_approval_required BOOLEAN NOT NULL DEFAULT true,
  created_by TEXT NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS content_assets (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  source_type TEXT NOT NULL,
  drive_file_id TEXT,
  file_name TEXT NOT NULL,
  mime_type TEXT,
  file_size_bytes BIGINT,
  parse_status TEXT NOT NULL DEFAULT 'queued',
  extracted_text TEXT,
  extracted_metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  task_type TEXT NOT NULL,
  task_key TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  retry_count INT NOT NULL DEFAULT 0,
  max_retries INT NOT NULL DEFAULT 3,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(job_id, task_key)
);

CREATE TABLE IF NOT EXISTS content_outputs (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  task_id UUID REFERENCES content_tasks(id),
  output_type TEXT NOT NULL,
  version INT NOT NULL DEFAULT 1,
  title TEXT NOT NULL,
  body_markdown TEXT,
  structured_data JSONB NOT NULL DEFAULT '{}'::jsonb,
  source_fact_map JSONB NOT NULL DEFAULT '[]'::jsonb,
  qa_status TEXT NOT NULL DEFAULT 'pending',
  drive_file_id TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_events (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  event_type TEXT NOT NULL,
  status_from job_status,
  status_to job_status,
  message TEXT NOT NULL,
  metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS content_errors (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  task_id UUID REFERENCES content_tasks(id),
  severity TEXT NOT NULL,
  error_code TEXT NOT NULL,
  error_message TEXT NOT NULL,
  recoverable BOOLEAN NOT NULL DEFAULT true,
  stack_trace TEXT,
  context JSONB NOT NULL DEFAULT '{}'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS content_approvals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  approval_stage TEXT NOT NULL,
  decision TEXT NOT NULL,
  reviewer_id TEXT NOT NULL,
  reviewer_notes TEXT,
  decided_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS job_messages (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  sender_type TEXT NOT NULL,
  sender_id TEXT,
  message_type TEXT NOT NULL,
  message_text TEXT,
  attachments JSONB NOT NULL DEFAULT '[]'::jsonb,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_jobs_status ON content_jobs(status);
CREATE INDEX IF NOT EXISTS idx_tasks_job_status ON content_tasks(job_id, status);
CREATE INDEX IF NOT EXISTS idx_outputs_job_type ON content_outputs(job_id, output_type);
CREATE INDEX IF NOT EXISTS idx_events_job_created ON content_events(job_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_errors_job_created ON content_errors(job_id, created_at DESC);
