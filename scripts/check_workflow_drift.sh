#!/usr/bin/env bash
set -euo pipefail
# Operator build workflows are authored in workflows/active and archived v1 workflows are immutable rollback references.
# This check intentionally avoids regenerating archived debug workflows and verifies no generated root-level import drift exists.
if find workflows -maxdepth 1 -type f -name '*.json' | rg -q '.json'; then
  echo "Root workflow JSON drift found. Active imports must live in workflows/active; archived v1 JSON must live in workflows/archive/v1_debug_build." >&2
  find workflows -maxdepth 1 -type f -name '*.json' >&2
  exit 1
fi
python - <<'PY'
import json
from pathlib import Path
for p in Path('workflows/active').glob('*.json'):
    json.loads(p.read_text())
print('workflow drift check ok')
PY
