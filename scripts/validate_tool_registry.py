#!/usr/bin/env python3
"""Validate the runtime tool registry against workflows and source-of-truth rules."""

from __future__ import annotations

import json
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ACTIVE_DIR = ROOT / "workflows" / "active"
REGISTRY_DIR = ROOT / "registry"
REQUIRED_TOOL_FIELDS = {
    "tool_id",
    "workflow_name",
    "version",
    "status",
    "category",
    "description",
    "capabilities",
    "input_contract",
    "output_contract",
    "required_credentials",
    "required_tables",
    "approval_policy",
    "agent_safe",
    "human_only",
    "can_run_in_dry_run",
    "cost_level",
    "average_runtime",
    "failure_mode",
    "tags",
}
ALLOWED_STATUSES = {"active", "disabled", "experimental", "deprecated"}
ALLOWED_FAILURE_MODES = {"recoverable", "retryable", "requires_human", "blocked_missing_input", "fatal"}
REQUIRED_CREDENTIALS = {
    "AI_AGENT_WEBHOOK_AUTH",
    "POSTGRES_AI_CONTENT_DB",
    "GOOGLE_DRIVE_AI_CONTENT",
    "AI_LLM_HTTP_AUTH",
}


def fail(message: str) -> None:
    print(f"TOOL REGISTRY FAILURE: {message}", file=sys.stderr)
    sys.exit(1)


def load_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as error:
        fail(f"{path.relative_to(ROOT)} is invalid JSON: {error}")


def active_workflow_names() -> set[str]:
    return {path.stem for path in ACTIVE_DIR.glob("*.json")}


def validate_tool(tool: dict, source: Path, workflow_names: set[str]) -> None:
    missing = REQUIRED_TOOL_FIELDS - set(tool)
    if missing:
        fail(f"{source.relative_to(ROOT)} tool {tool.get('tool_id', '<unknown>')} missing fields: {sorted(missing)}")

    status = tool["status"]
    if status not in ALLOWED_STATUSES:
        fail(f"{tool['tool_id']} has invalid status {status!r}")
    if tool["failure_mode"] not in ALLOWED_FAILURE_MODES:
        fail(f"{tool['tool_id']} has invalid failure_mode {tool['failure_mode']!r}")

    for key in ("capabilities", "required_credentials", "required_tables", "tags"):
        if not isinstance(tool[key], list):
            fail(f"{tool['tool_id']} field {key} must be a list")
    for key in ("input_contract", "output_contract"):
        if not isinstance(tool[key], dict):
            fail(f"{tool['tool_id']} field {key} must be an object")

    if status == "active":
        workflow_name = tool["workflow_name"]
        if workflow_name not in workflow_names:
            fail(f"active tool {tool['tool_id']} points to missing workflow {workflow_name}")
        unknown_credentials = set(tool["required_credentials"]) - REQUIRED_CREDENTIALS
        if unknown_credentials:
            fail(f"{tool['tool_id']} references unknown credential(s): {sorted(unknown_credentials)}")
        if not tool["capabilities"]:
            fail(f"{tool['tool_id']} must define at least one capability")
        if tool["human_only"] and tool["agent_safe"]:
            fail(f"{tool['tool_id']} cannot be both human_only and agent_safe")


def main() -> None:
    workflow_names = active_workflow_names()
    active_registry = load_json(REGISTRY_DIR / "tools.active.json")
    disabled_registry = load_json(REGISTRY_DIR / "tools.disabled.json")
    experimental_registry = load_json(REGISTRY_DIR / "tools.experimental.json")
    infrastructure = load_json(REGISTRY_DIR / "infrastructure_workflows.json")

    all_tools = []
    seen_tool_ids: set[str] = set()
    seen_workflow_names: set[str] = set()
    for source, registry in [
        (REGISTRY_DIR / "tools.active.json", active_registry),
        (REGISTRY_DIR / "tools.disabled.json", disabled_registry),
        (REGISTRY_DIR / "tools.experimental.json", experimental_registry),
    ]:
        tools = registry.get("tools")
        if not isinstance(tools, list):
            fail(f"{source.relative_to(ROOT)} must contain a tools array")
        for tool in tools:
            validate_tool(tool, source, workflow_names)
            if tool["tool_id"] in seen_tool_ids:
                fail(f"duplicate tool_id {tool['tool_id']}")
            seen_tool_ids.add(tool["tool_id"])
            if tool["status"] == "active":
                seen_workflow_names.add(tool["workflow_name"])
            all_tools.append(tool)

    infrastructure_names = {
        item.get("workflow_name")
        for item in infrastructure.get("workflows", [])
        if item.get("planner_selectable") is False
    }
    missing_marker = workflow_names - seen_workflow_names - infrastructure_names
    if missing_marker:
        fail(f"active workflow(s) neither registered nor infrastructure-only: {sorted(missing_marker)}")

    selectable_infrastructure = seen_workflow_names & infrastructure_names
    if selectable_infrastructure:
        fail(f"infrastructure workflow(s) must not be registered as active tools: {sorted(selectable_infrastructure)}")

    if len([tool for tool in all_tools if tool["status"] == "active"]) < 1:
        fail("at least one active tool is required")

    print("tool registry validation ok")


if __name__ == "__main__":
    main()
