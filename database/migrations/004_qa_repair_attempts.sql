CREATE TABLE IF NOT EXISTS content_repair_attempts (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id UUID NOT NULL REFERENCES content_jobs(id) ON DELETE CASCADE,
  output_id UUID REFERENCES content_outputs(id) ON DELETE SET NULL,
  repair_type TEXT NOT NULL,
  issue_code TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'queued',
  attempt_number INT NOT NULL DEFAULT 1,
  max_attempts INT NOT NULL DEFAULT 2,
  input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
  error_message TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ
);

CREATE INDEX IF NOT EXISTS idx_repair_attempts_job_status ON content_repair_attempts(job_id, status);
