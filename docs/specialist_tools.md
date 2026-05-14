# Specialist Tool Roadmap

The broad `tool_content_generation` workflow remains the active production fallback. The v2.7 specialist tools are registered as experimental contracts first so the planner cannot select them in production until each has a workflow ID, credential check, dry-run test, and live limited test.

## Promotion Checklist

1. Create the workflow JSON in `workflows/active/` only when it is ready to deploy.
2. Add the n8n workflow ID to the GitHub deploy mapping.
3. Move the registry entry from `registry/tools.experimental.json` to `registry/tools.active.json`.
4. Add a dry-run payload and expected status check.
5. Run the full validation and deployment checks.
6. Prove the generic fallback still works.

## Experimental Tools

- `tool_generate_social_posts`
- `tool_generate_blog_article`
- `tool_generate_email_campaign`
- `tool_generate_image_briefs`
- `tool_generate_video_script`
- `tool_qa_claim_checker`
- `tool_qa_brand_checker`
- `tool_delivery_packager`

## Current Runtime Behavior

Until these tools are promoted to active, planner output must continue using `tool_content_generation` and `tool_qa_delivery`. Missing specialist capability should be recorded honestly instead of inventing or selecting inactive tools.
