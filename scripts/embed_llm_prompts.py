#!/usr/bin/env python3
"""Embed task-specific prompts into generated LLM workflow JSON.

The LLM workflow generator originally produced generic prompt-file references such
as `Use prompt file prompts/social_posts.md`. This script rewrites those generated
Build Model Request code nodes so live model calls carry real task instructions.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"

PROMPTS = {
    "analyse_client_request": "Analyse the client brief and available assets. Return strict JSON with facts, assumptions, missing_information, risk_flags, requested_outputs, source_material_used, and human_review_required. Do not invent dates, prices, locations, claims, guarantees, testimonials, endorsements, or product details.",
    "generate_content_plan": "Create a practical content plan from the approved analysis. Return strict JSON with strategy_summary, audience, tone, content_pillars, outputs, dependencies, missing_information, risk_flags, source_material_used, and human_review_required. Only use supported facts.",
    "generate_campaign_plan": "Generate a campaign plan. Return strict JSON with campaign_name, objective, phases, channels, deliverables, assumptions, missing_information, unsupported_claims, and source_material_used. Keep claims modest and evidence-bound.",
    "generate_social_posts": "Generate social media post copy. Return strict JSON with a posts array. Each post must include platform, copy, purpose, source_material_used, assumptions, missing_information, and notes. Do not invent specific dates, prices, venues, claims, endorsements, or testimonials.",
    "generate_email_copy": "Generate email copy. Return strict JSON with subject, preview_text, body, cta, assumptions, missing_information, source_material_used, and human_review_required. Avoid unsupported claims.",
    "generate_blog_article_copy": "Generate blog or article copy. Return strict JSON with title, body_markdown, sections, facts_used, assumptions, missing_information, source_material_used, and human_review_required. Flag any claim that needs client confirmation.",
    "generate_image_prompts": "Generate image generation prompts. Return strict JSON with prompts array and must_avoid array. Each prompt must avoid implying real locations, people, endorsements, product facts, or claims unless supplied in source material.",
    "generate_video_scripts": "Generate short video scripts, shot lists, storyboard notes, and CapCut-ready edit notes. Return strict JSON with video_scripts array, shot_lists, storyboard_notes, edit_notes, assumptions, missing_information, and source_material_used.",
    "qa_check_outputs": "QA-check pending outputs against the brief, source material, assumptions, and missing information. Return strict JSON with overall_status, checks array, unsupported_claims, missing_information, required_revisions, approval_recommendation, and human_review_required.",
}

GENERIC_PROMPT_RE = re.compile(r"const prompt = `You are running workflow .*?`;", re.DOTALL)


def embed_prompt(path: Path, workflow_name: str) -> bool:
    data = json.loads(path.read_text())
    prompt = PROMPTS[workflow_name]
    changed = False
    for node in data.get("nodes", []):
        if node.get("name") != "Build Model Request":
            continue
        params = node.setdefault("parameters", {})
        js = params.get("jsCode", "")
        replacement = "const prompt = " + json.dumps(prompt) + ";"
        new_js = GENERIC_PROMPT_RE.sub(replacement, js)
        if new_js != js:
            params["jsCode"] = new_js
            changed = True
    if changed:
        path.write_text(json.dumps(data, indent=2) + "\n")
    return changed


def main() -> None:
    changed = []
    missing = []
    for workflow_name in PROMPTS:
        path = WORKFLOWS / f"{workflow_name}.json"
        if not path.exists():
            missing.append(str(path))
            continue
        if embed_prompt(path, workflow_name):
            changed.append(str(path))
    if missing:
        raise SystemExit("Missing generated LLM workflows:\n" + "\n".join(missing))
    if changed:
        print("Embedded task prompts in:")
        for item in changed:
            print(f"- {item}")
    else:
        print("No generic LLM prompt references needed embedding.")


if __name__ == "__main__":
    main()
