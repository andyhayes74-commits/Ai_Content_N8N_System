# Sandbox Test Plan

1. Call `create_content_job` with `examples/client_brief.json`.
2. Copy the returned UUID into later fixtures.
3. Call `analyse_client_request`, then `api_approve_analysis`.
4. Call `generate_content_plan`, then `api_approve_plan`.
5. Call `route_output_tasks` and `generate_social_posts` with dry-run/generated payloads.
6. Call `qa_check_outputs`.
7. Call `api_approve_final_delivery` with `reviewer_type='human'`.
8. Call `generate_delivery_pack` and confirm the job reaches `delivery_ready`.
