#!/usr/bin/env bash
set -euo pipefail

PYTHON_BIN="${PYTHON_BIN:-}"
if [ -z "$PYTHON_BIN" ]; then
  if command -v python3 >/dev/null 2>&1; then
    PYTHON_BIN="python3"
  elif command -v python >/dev/null 2>&1; then
    PYTHON_BIN="python"
  else
    echo "Python 3 is required for n8n import preflight." >&2
    exit 1
  fi
fi

ACTIVE_DIR="workflows/active"
"$PYTHON_BIN" scripts/static_workflow_audit.py >/dev/null
"$PYTHON_BIN" scripts/pre_n8n_readiness_check.py >/dev/null

if ! command -v n8n >/dev/null 2>&1; then
  echo "n8n CLI is not installed. Install n8n or run this in the GitHub Action/preflight container." >&2
  exit 1
fi

n8n import:workflow --separate --input="${ACTIVE_DIR}/"

echo "n8n import preflight completed against ${ACTIVE_DIR}. This validates import shape only, not credentials or live node execution."
