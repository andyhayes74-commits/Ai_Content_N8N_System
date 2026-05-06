#!/usr/bin/env bash
set -euo pipefail

if ! git rev-parse --is-inside-work-tree >/dev/null 2>&1; then
  echo "workflow drift check skipped: not inside a git work tree"
  exit 0
fi

if ! git diff --quiet -- workflows/; then
  echo "Workflow drift detected: generated workflow files differ from committed workflows." >&2
  echo "Run the workflow generators, review workflows/, and commit the resulting JSON before transfer/import." >&2
  echo "Generator sequence:" >&2
  echo "  python scripts/build_llm_workflows.py" >&2
  echo "  python scripts/embed_llm_prompts.py" >&2
  echo "  python scripts/build_drive_workflows.py" >&2
  echo "  python scripts/fix_generated_n8n_expressions.py" >&2
  git diff --stat -- workflows/ >&2
  exit 1
fi

echo "workflow drift check ok"
