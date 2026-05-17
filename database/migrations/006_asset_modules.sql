CREATE TABLE IF NOT EXISTS content_asset_modules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  client_profile_id UUID REFERENCES client_profiles(id) ON DELETE CASCADE,
  job_id UUID REFERENCES content_jobs(id) ON DELETE SET NULL,
  module_key TEXT NOT NULL,
  module_type TEXT NOT NULL,
  status TEXT NOT NULL DEFAULT 'active',
  compatibility_tags JSONB NOT NULL DEFAULT '[]'::jsonb,
  usage_rules JSONB NOT NULL DEFAULT '{}'::jsonb,
  source_files JSONB NOT NULL DEFAULT '[]'::jsonb,
  generated_assets JSONB NOT NULL DEFAULT '[]'::jsonb,
  prompt_context JSONB NOT NULL DEFAULT '{}'::jsonb,
  version INT NOT NULL DEFAULT 1,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE(client_profile_id, module_key, version)
);

CREATE INDEX IF NOT EXISTS idx_asset_modules_client_status ON content_asset_modules(client_profile_id, status);
