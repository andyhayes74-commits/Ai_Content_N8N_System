#!/usr/bin/env python3
"""Deprecated generator retained as an operator guardrail.

The active v2 workflows are maintained in workflows/active and use n8n
credentials only. The old generator emitted env-based workflow fragments, so it
now exits with guidance instead of producing outdated JSON.
"""
from __future__ import annotations

raise SystemExit(
    "build_drive_workflows.py is deprecated. Edit workflows/active directly and "
    "attach GOOGLE_DRIVE_AI_CONTENT in n8n."
)
