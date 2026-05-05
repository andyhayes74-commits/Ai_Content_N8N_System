#!/usr/bin/env bash
set -euo pipefail

# This script checks n8n import-shape compatibility before the workflows touch Andy's server.
# It requires the n8n CLI to be available in the execution environment.

if ! command -v n8n >/dev/null 2>&1; then
  echo "n8n CLI is not installed. Install n8n or run this in the GitHub Action/preflight container." >&2
  exit 1
fi

EXPORT_DIR="${N8N_IMPORT_PREFLIGHT_DIR:-/tmp/ai-content-n8n-preflight}"
rm -rf "$EXPORT_DIR"
mkdir -p "$EXPORT_DIR"

n8n import:workflow --separate --input=workflows/

echo "n8n import preflight completed. This validates import shape only, not credentials or live node execution."
