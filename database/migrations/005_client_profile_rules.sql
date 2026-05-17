ALTER TABLE client_profiles
  ADD COLUMN IF NOT EXISTS brand_voice JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS tone_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS approved_claims JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS forbidden_claims JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS product_families JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS output_defaults JSONB NOT NULL DEFAULT '{}'::jsonb,
  ADD COLUMN IF NOT EXISTS default_approval_policy TEXT NOT NULL DEFAULT 'full_staged',
  ADD COLUMN IF NOT EXISTS asset_roots JSONB NOT NULL DEFAULT '[]'::jsonb,
  ADD COLUMN IF NOT EXISTS delivery_preferences JSONB NOT NULL DEFAULT '{}'::jsonb;

UPDATE client_profiles
SET default_approval_policy = 'full_staged'
WHERE default_approval_policy IS NULL OR default_approval_policy = '';
