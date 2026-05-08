-- Non-breaking metadata column for operator architecture approval safety checks.
ALTER TABLE content_approvals
  ADD COLUMN IF NOT EXISTS reviewer_type TEXT NOT NULL DEFAULT 'human';
