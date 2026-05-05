-- Replace :job_id with the sandbox job UUID before running.

SELECT id, project_name, status
FROM content_jobs
WHERE id = :'job_id'::uuid;

SELECT task_key, status, retry_count
FROM content_tasks
WHERE job_id = :'job_id'::uuid
ORDER BY created_at;

SELECT output_type, title, qa_status, drive_file_id
FROM content_outputs
WHERE job_id = :'job_id'::uuid
ORDER BY created_at;

SELECT approval_stage, decision, reviewer_id, decided_at
FROM content_approvals
WHERE job_id = :'job_id'::uuid
ORDER BY decided_at;

SELECT event_type, message, created_at
FROM content_events
WHERE job_id = :'job_id'::uuid
ORDER BY created_at;

SELECT severity, error_code, error_message, recoverable, resolved_at
FROM content_errors
WHERE job_id = :'job_id'::uuid
ORDER BY created_at;

-- Expected final checks after a full dry-run path:
SELECT COUNT(*) >= 1 AS has_job
FROM content_jobs
WHERE id = :'job_id'::uuid;

SELECT COUNT(*) >= 3 AS has_approval_gates
FROM content_approvals
WHERE job_id = :'job_id'::uuid
  AND approval_stage IN ('analysis', 'plan', 'final_delivery')
  AND decision = 'approved';

SELECT COUNT(*) >= 1 AS has_delivery_pack
FROM content_outputs
WHERE job_id = :'job_id'::uuid
  AND output_type = 'delivery_pack';

SELECT status = 'delivery_ready' AS is_delivery_ready
FROM content_jobs
WHERE id = :'job_id'::uuid;

SELECT COUNT(*) = 0 AS no_open_critical_errors
FROM content_errors
WHERE job_id = :'job_id'::uuid
  AND severity = 'critical'
  AND resolved_at IS NULL;
