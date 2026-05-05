# Sandbox Test Plan
1. Configure n8n credentials: `POSTGRES_AI_CONTENT_DB`, `GOOGLE_DRIVE_AI_CONTENT`, `HTTP_OPENAI_OR_LITELLM`.
2. Import all workflows.
3. POST fixture to `/v1/create_content_job`.
4. Register or create drive folder workflows.
5. Run scan/parse/describe/audio-video/create_asset_index.
6. Run analyse_client_request then approve analysis.
7. Run generate_content_plan then approve plan.
8. Run route_output_tasks and generation workflows.
9. Run qa_check_outputs.
10. Insert final_delivery approval (human `andy`) then run generate_delivery_pack.
11. Run notify_user_for_review.
