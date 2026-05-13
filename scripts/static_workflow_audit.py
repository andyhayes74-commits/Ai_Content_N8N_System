#!/usr/bin/env python3
"""Static audit for the n8n-credentials-only operator workflow set."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ACTIVE = Path("workflows/active")
ARCHIVE = Path("workflows/archive/v1_debug_build")
REQUIRED = {
    "ai_content_orchestrator",
    "tool_job_intake",
    "tool_drive_assets",
    "tool_request_analysis",
    "tool_content_planning",
    "tool_content_generation",
    "tool_qa_delivery",
    "tool_logging",
    "api_supervisor_gateway",
    "api_human_review_gateway",
}
LLM_TOOLS = ["tool_request_analysis", "tool_content_planning", "tool_content_generation", "tool_qa_delivery"]
REQUIRED_OUTPUT_TYPES = ["campaign_plan", "social_posts", "email_copy", "blog_article", "image_prompts", "video_scripts"]
SECRET_PATTERNS = re.compile(r"sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-")
FORBIDDEN = re.compile(
    r"DELETE FROM|DROP TABLE|TRUNCATE|publish content|send final|final client deliverables|"
    r"change credentials|modify database schema|edit n8n workflows directly",
    re.I,
)
BAD_EXPR = re.compile(r"\|\|\s*}}|(?<!\{)\{\$json|\{\{\$json\.[A-Za-z0-9_]+\}(?!\})|template action")


def fail(message: str) -> None:
    print(f"AUDIT FAILURE: {message}", file=sys.stderr)
    raise SystemExit(1)


def load(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception as exc:
        fail(f"Invalid workflow JSON {path}: {exc}")


def nodes(data: dict, type_name: str | None = None) -> list[dict]:
    found = data.get("nodes", [])
    if type_name:
        return [node for node in found if node.get("type") == type_name]
    return found


def code_nodes(data: dict):
    for item in nodes(data, "n8n-nodes-base.code"):
        yield item.get("name", "<unnamed>"), item.get("parameters", {}).get("jsCode", "")


def likely_unreachable(js: str) -> bool:
    depth = 0
    lines = js.splitlines()
    for idx, line in enumerate(lines):
        stripped = line.strip()
        if not stripped or stripped.startswith("//"):
            continue
        before_depth = depth
        if re.search(r"(^|[;\s])return\b", stripped) and before_depth == 0:
            for later in lines[idx + 1 :]:
                later = later.strip()
                if later and not later.startswith("//"):
                    return True
        depth += line.count("{") - line.count("}")
        depth = max(depth, 0)
    return False


def has_credential(node: dict, key: str) -> bool:
    credential = node.get("credentials", {}).get(key, {})
    return bool(credential.get("name"))


def connection_targets(data: dict, source: str) -> list[str]:
    connection = data.get("connections", {}).get(source, {}).get("main", [])
    targets: list[str] = []
    for output in connection:
        targets.extend(item.get("node", "") for item in output)
    return targets


def assert_service_credentials(path: Path, data: dict) -> None:
    for item in nodes(data):
        node_type = item.get("type")
        name = item.get("name", "<unnamed>")
        if node_type == "n8n-nodes-base.webhook" and not has_credential(item, "httpHeaderAuth"):
            fail(f"{path.name} webhook {name!r} must use n8n header-auth credentials")
        if node_type == "n8n-nodes-base.postgres" and not has_credential(item, "postgres"):
            fail(f"{path.name} Postgres node {name!r} must declare POSTGRES_AI_CONTENT_DB credential")
        if node_type == "n8n-nodes-base.googleDrive" and not (
            has_credential(item, "googleApi") or has_credential(item, "googleDriveOAuth2Api")
        ):
            fail(f"{path.name} Drive node {name!r} must declare GOOGLE_DRIVE_AI_CONTENT credential")
        if node_type == "n8n-nodes-base.httpRequest":
            params = item.get("parameters", {})
            if params.get("authentication") == "predefinedCredentialType":
                credential_key = params.get("nodeCredentialType")
                if credential_key and not has_credential(item, credential_key):
                    fail(f"{path.name} HTTP node {name!r} must declare n8n credential {credential_key}")


def assert_gate(data: dict, query_node: str, if_node: str, blocked_node: str) -> None:
    if if_node not in connection_targets(data, query_node):
        fail(f"{data.get('name')} must branch from {query_node!r} into {if_node!r}")
    targets = connection_targets(data, if_node)
    if blocked_node not in targets:
        fail(f"{data.get('name')} must send unapproved gate output to {blocked_node!r}")


def main() -> int:
    active_files = sorted(ACTIVE.glob("*.json"))
    found = {path.stem for path in active_files}
    missing = REQUIRED - found
    if missing:
        fail(f"Missing active workflows: {sorted(missing)}")
    if not 8 <= len(active_files) <= 14:
        fail(f"Active workflow count must be between 8 and 14, found {len(active_files)}")
    if len(list(ARCHIVE.glob("*.json"))) < 35:
        fail("Archived v1 debug workflows are missing or incomplete")

    all_text = ""
    summaries = []
    for path in active_files:
        data = load(path)
        text = path.read_text()
        all_text += "\n" + text
        if "{{{" in text or "}}}" in text:
            fail(f"{path.name} has malformed triple-brace n8n expression syntax")
        if "$env" in text:
            fail(f"{path.name} still references environment variables; use n8n credentials or payload fields")
        if SECRET_PATTERNS.search(text):
            fail(f"Possible hardcoded secret found in {path.name}")
        if FORBIDDEN.search(text):
            fail(f"Forbidden destructive/publish/send pattern found in {path.name}")
        if BAD_EXPR.search(text):
            fail(f"Malformed expression or placeholder action in {path.name}")
        assert_service_credentials(path, data)
        for node_name, js in code_nodes(data):
            if likely_unreachable(js):
                fail(f"{path.name} code node {node_name!r} has likely unreachable code after unconditional return")
        summaries.append(
            {
                "workflow": path.name,
                "webhook_paths": [n.get("parameters", {}).get("path", "") for n in nodes(data, "n8n-nodes-base.webhook")],
                "tables": sorted(set(re.findall(r"\b(content_[a-z_]+|client_profiles|job_messages)\b", text))),
                "uses_n8n_credentials": True,
            }
        )

    orchestrator = load(ACTIVE / "ai_content_orchestrator.json")
    orchestrator_text = (ACTIVE / "ai_content_orchestrator.json").read_text()
    for tool in sorted(w for w in REQUIRED if w.startswith("tool_")):
        if tool not in orchestrator_text:
            fail(f"Orchestrator does not call {tool}")
    for marker in ["desired_tools", "tool_results", "current_stage", "payload", "dry_run_full_lifecycle"]:
        if marker not in orchestrator_text:
            fail(f"Orchestrator missing state/routing marker: {marker}")

    generation = (ACTIVE / "tool_content_generation.json").read_text()
    for output_type in REQUIRED_OUTPUT_TYPES:
        if output_type not in generation:
            fail(f"Content generation dispatch missing output type: {output_type}")

    for name in LLM_TOOLS:
        data = load(ACTIVE / f"{name}.json")
        text = (ACTIVE / f"{name}.json").read_text()
        for marker in ["Is Live Mode", "Parse LLM Response", "choices?.[0]?.message?.content", "content_errors"]:
            if marker not in text:
                fail(f"{name} lacks marker: {marker}")
        if "Parse LLM Response" not in connection_targets(data, "Is Live Mode"):
            fail(f"{name} dry-run branch must bypass the LLM HTTP node and go to Parse LLM Response")

    planning = load(ACTIVE / "tool_content_planning.json")
    generation_data = load(ACTIVE / "tool_content_generation.json")
    qa = load(ACTIVE / "tool_qa_delivery.json")
    assert_gate(planning, "Require Analysis Approval", "Analysis Approved", "Return Waiting For Analysis Approval")
    assert_gate(generation_data, "Require Plan Approval", "Plan Approved", "Return Waiting For Plan Approval")
    assert_gate(qa, "Require Final Approval", "Final Human Approved", "Return Waiting For Final Approval")

    for marker in [
        "approval_stage='analysis'",
        "approval_stage='plan'",
        "approval_stage='final_delivery'",
        "reviewer_type='human'",
        "waiting_for_analysis_approval",
        "waiting_for_plan_approval",
        "waiting_for_human_review",
    ]:
        if marker not in all_text:
            fail(f"Missing approval gate marker: {marker}")

    supervisor = (ACTIVE / "api_supervisor_gateway.json").read_text()
    for forbidden_action in ["delete_files", "publish_content", "send_final", "change_credentials", "modify_schema", "edit_workflows", "approve_final_delivery"]:
        if forbidden_action not in supervisor:
            fail(f"Supervisor safety boundary missing forbidden action: {forbidden_action}")

    for summary in summaries:
        print(summary)
    print("static workflow audit passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
