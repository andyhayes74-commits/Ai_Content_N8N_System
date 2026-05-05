# Failure Recovery
- Log all failures to `content_errors` with recoverable flag.
- Emit `content_events` at each transition.
- Use `retry_safe_failed_steps` for idempotent operations only.
- For non-recoverable errors: set `content_jobs.status='failed'` and notify supervisor.
- For pause/resume/cancel operations, write status and event atomically.
