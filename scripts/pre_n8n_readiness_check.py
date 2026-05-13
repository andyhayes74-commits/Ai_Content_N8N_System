#!/usr/bin/env python3
"""Pre-n8n readiness checks for the usable automation baseline."""
from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ACTIVE = ROOT / "workflows" / "active"
ARCHIVE = ROOT / "workflows" / "archive" / "v1_debug_build"
REQUIRED_WORKFLOWS = [
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
]
REQUIRED_CREDENTIAL_NAMES = {
    "POSTGRES_AI_CONTENT_DB",
    "GOOGLE_DRIVE_AI_CONTENT",
    "AI_LLM_HTTP_AUTH",
    "AI_AGENT_WEBHOOK_AUTH",
}
SECRET_PATTERNS = re.compile(r"sk-[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,}|xox[baprs]-")
FORBIDDEN = re.compile(
    r"DELETE FROM|DROP TABLE|TRUNCATE|publish content|send final|final client deliverables|"
    r"change credentials|modify database schema|edit n8n workflows directly",
    re.I,
)
failures: list[str] = []


def fail(message: str) -> None:
    failures.append(message)


def load(name: str) -> tuple[dict, str]:
    path = ACTIVE / f"{name}.json"
    if not path.exists():
        fail(f"Missing workflow: {path}")
        return {}, ""
    text = path.read_text()
    try:
        return json.loads(text), text
    except Exception as exc:
        fail(f"Invalid JSON in {path}: {exc}")
        return {}, text


def node_types(data: dict) -> set[str]:
    return {node.get("type", "") for node in data.get("nodes", [])}


def credential_names(data: dict) -> set[str]:
    names = set()
    for node in data.get("nodes", []):
        for credential in node.get("credentials", {}).values():
            if credential.get("name"):
                names.add(credential["name"])
    return names


def main() -> int:
    if (ROOT / ".env.example").exists():
        fail(".env.example must not exist; configure secrets only through n8n credentials")
    active_count = len(list(ACTIVE.glob("*.json")))
    if not 8 <= active_count <= 14:
        fail(f"Active workflow count outside 8-14: {active_count}")
    if len(list(ARCHIVE.glob("*.json"))) < 35:
        fail("v1 debug workflows are not archived")

    active_text = "\n".join(path.read_text() for path in ACTIVE.glob("*.json"))
    if "$env" in active_text:
        fail("Active workflows still reference $env; use n8n credentials or payload fields")
    if SECRET_PATTERNS.search(active_text):
        fail("Possible hardcoded secret found in active workflows")

    seen_credentials: set[str] = set()
    for name in REQUIRED_WORKFLOWS:
        data, text = load(name)
        if FORBIDDEN.search(text):
            fail(f"Forbidden destructive/send/publish term found in {name}")
        seen_credentials |= credential_names(data)

    missing_credentials = REQUIRED_CREDENTIAL_NAMES - seen_credentials
    if missing_credentials:
        fail(f"Required n8n credential names are not declared in workflows: {sorted(missing_credentials)}")

    audit = subprocess.run(
        [sys.executable, str(ROOT / "scripts/static_workflow_audit.py")],
        cwd=ROOT,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if audit.returncode != 0:
        fail("static workflow audit failed:\n" + audit.stdout + audit.stderr)

    orchestrator = (ACTIVE / "ai_content_orchestrator.json").read_text()
    for marker in ["desired_tools", "tool_results", "current_stage", "dry_run_full_lifecycle"]:
        if marker not in orchestrator:
            fail(f"Orchestrator missing state/routing marker: {marker}")

    for name in ["tool_request_analysis", "tool_content_planning", "tool_content_generation", "tool_qa_delivery"]:
        data, text = load(name)
        types = node_types(data)
        if "n8n-nodes-base.httpRequest" not in types:
            fail(f"LLM-capable tool lacks HTTP Request node: {name}")
        for marker in ["Is Live Mode", "Parse LLM Response", "choices?.[0]?.message?.content", "content_errors"]:
            if marker not in text:
                fail(f"LLM-capable tool lacks marker {marker}: {name}")

    for name in ["tool_drive_assets", "tool_qa_delivery"]:
        data, _ = load(name)
        if "n8n-nodes-base.googleDrive" not in node_types(data):
            fail(f"Drive tool lacks Google Drive node: {name}")

    all_text = "\n".join((ACTIVE / f"{name}.json").read_text() for name in REQUIRED_WORKFLOWS if (ACTIVE / f"{name}.json").exists())
    for marker in ["waiting_for_analysis_approval", "waiting_for_plan_approval", "waiting_for_human_review", "final_delivery", "reviewer_type"]:
        if marker not in all_text:
            fail(f"Missing safety/approval marker: {marker}")

    for doc in ["docs/tool_registry.md", "docs/deployment_model.md", "docs/architecture.md", "docs/failure_recovery.md", "docs/setup_guide.md"]:
        if not (ROOT / doc).exists():
            fail(f"Missing doc: {doc}")
    for fixture in [
        "tests/payloads/01_orchestrator_dry_run_job.json",
        "tests/payloads/02_supervisor_status_check.json",
        "tests/payloads/03_human_analysis_approval.json",
        "tests/payloads/04_generation_route.json",
        "tests/payloads/05_qa_delivery_route.json",
    ]:
        if not (ROOT / fixture).exists():
            fail(f"Missing dry-run payload: {fixture}")

    import_text = (ROOT / "scripts/n8n_import_preflight.sh").read_text()
    if "workflows/active" not in import_text or "--input=workflows/" in import_text:
        fail("n8n import preflight does not target workflows/active only")

    if failures:
        print("Pre-n8n readiness check FAILED:\n")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print("Pre-n8n readiness check passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
