#!/usr/bin/env python3
"""Pre-n8n readiness checks for the AI Content n8n System.

This script is intentionally stricter than validate_repo.sh. It checks whether the
repository is ready to leave GitHub for n8n sandbox import. It does not prove live
credential execution, but it should block obvious dry-run-only or placeholder-only
workflow states.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"
ENV_EXAMPLE = ROOT / ".env.example"

LLM_WORKFLOWS = [
    "analyse_client_request",
    "generate_content_plan",
    "generate_campaign_plan",
    "generate_social_posts",
    "generate_email_copy",
    "generate_blog_article_copy",
    "generate_image_prompts",
    "generate_video_scripts",
    "qa_check_outputs",
]

DRIVE_WORKFLOWS = [
    "create_new_drive_project_folder",
    "create_standard_folder_structure",
    "scan_drive_assets",
    "parse_and_summarise_documents",
    "create_asset_index",
    "generate_delivery_pack",
]

REQUIRED_ENV = [
    "POSTGRES_HOST",
    "POSTGRES_PORT",
    "POSTGRES_DB",
    "POSTGRES_USER",
    "POSTGRES_PASSWORD",
    "GOOGLE_DRIVE_CREDENTIAL_ID",
    "DEFAULT_PARENT_DRIVE_FOLDER_ID",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
    "LITELLM_BASE_URL",
    "LITELLM_API_KEY",
    "AGENT_WEBHOOK_SECRET",
    "NOTIFICATION_WEBHOOK_URL",
]

FORBIDDEN = re.compile(r"DELETE FROM|DROP TABLE|TRUNCATE|send final|client deliver|publish", re.I)
SECRET_PATTERNS = re.compile(r"sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-")
BAD_EXPR = re.compile(r"\|\|\s*}}|\{\$json|\$json\.body\.job_id\s*\|\||template action|NULLIF\('\{\$json")

failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)


def load_workflow(name: str) -> tuple[dict, str]:
    path = WORKFLOWS / f"{name}.json"
    if not path.exists():
        fail(f"Missing workflow: {path}")
        return {}, ""
    text = path.read_text()
    try:
        data = json.loads(text)
    except Exception as exc:
        fail(f"Invalid JSON in {path}: {exc}")
        return {}, text
    return data, text


def node_types(data: dict) -> set[str]:
    return {node.get("type", "") for node in data.get("nodes", [])}


def check_env() -> None:
    text = ENV_EXAMPLE.read_text() if ENV_EXAMPLE.exists() else ""
    for key in REQUIRED_ENV:
        if f"{key}=" not in text:
            fail(f"Missing .env.example placeholder: {key}")


def check_common(name: str, text: str) -> None:
    if BAD_EXPR.search(text):
        fail(f"Malformed n8n expression/template marker in {name}")
    if FORBIDDEN.search(text):
        fail(f"Forbidden destructive/send/publish term found in {name}")
    if SECRET_PATTERNS.search(text):
        fail(f"Possible hardcoded secret found in {name}")
    if "x-agent-secret" not in text and "X-Agent-Secret" not in text:
        fail(f"Workflow lacks agent secret check: {name}")


def check_llm_workflows() -> None:
    for name in LLM_WORKFLOWS:
        data, text = load_workflow(name)
        check_common(name, text)
        types = node_types(data)
        if "n8n-nodes-base.httpRequest" not in types:
            fail(f"LLM workflow lacks HTTP Request node: {name}")
        if "OPENAI_API_KEY" not in text and "LITELLM_API_KEY" not in text:
            fail(f"LLM workflow lacks model credential env reference: {name}")
        if "LITELLM_BASE_URL" not in text and "api.openai.com" not in text:
            fail(f"LLM workflow lacks model endpoint reference: {name}")
        if "INSERT INTO content_outputs" not in text:
            fail(f"LLM workflow does not persist content_outputs: {name}")
        if "content_errors" not in text:
            fail(f"LLM workflow lacks content_errors failure path marker: {name}")
        if "dry_run_fallback" in text and "n8n-nodes-base.httpRequest" not in types:
            fail(f"LLM workflow appears dry-run only: {name}")


def check_drive_workflows() -> None:
    for name in DRIVE_WORKFLOWS:
        data, text = load_workflow(name)
        check_common(name, text)
        types = node_types(data)
        has_drive_node = "n8n-nodes-base.googleDrive" in types or "n8n-nodes-base.httpRequest" in types
        if not has_drive_node:
            fail(f"Drive workflow lacks Google Drive or HTTP Request node: {name}")
        if "GOOGLE_DRIVE" not in text and "DEFAULT_PARENT_DRIVE_FOLDER_ID" not in text and "drive" not in text.lower():
            fail(f"Drive workflow lacks Drive credential/config marker: {name}")


def main() -> int:
    check_env()
    for path in sorted(WORKFLOWS.glob("*.json")):
        text = path.read_text()
        try:
            json.loads(text)
        except Exception as exc:
            fail(f"Invalid workflow JSON {path.name}: {exc}")
        check_common(path.name, text)
    check_llm_workflows()
    check_drive_workflows()
    if failures:
        print("Pre-n8n readiness check FAILED:\n")
        for item in failures:
            print(f"- {item}")
        return 1
    print("Pre-n8n readiness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
