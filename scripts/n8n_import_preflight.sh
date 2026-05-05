#!/usr/bin/env bash
set -euo pipefail

python scripts/build_llm_workflows.py >/dev/null

if ! command -v n8n >/dev/null 2>&1; then
  echo "n8n CLI is not installed. Install n8n or run this in the GitHub Action/preflight container." >&2
  exit 1
fi

n8n import:workflow --separate --input=workflows/

echo "n8n import preflight completed. This validates import shape only, not credentials or live node execution."
