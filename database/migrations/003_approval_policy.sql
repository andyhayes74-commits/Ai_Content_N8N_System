-- Non-breaking v2.3 approval policy support.

ALTER TABLE content_jobs
  ADD COLUMN IF NOT EXISTS approval_policy TEXT NOT NULL DEFAULT 'full_staged';

UPDATE content_jobs
SET approval_policy = 'full_staged'
WHERE approval_policy IS NULL OR approval_policy = '';
