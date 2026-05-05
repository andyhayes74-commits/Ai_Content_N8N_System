#!/usr/bin/env python3
"""Repair n8n expression braces after Python f-string based workflow generation.

Python f-strings collapse `{{$json.foo}}` to `{$json.foo}` unless every brace is
quadruple-escaped. Rather than relying on fragile escaping across long generated
SQL and response templates, this post-generation repair pass restores single-brace
n8n expressions that start with `$` back to valid double-brace expressions.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WORKFLOWS = ROOT / "workflows"
SINGLE_BRACE_EXPR = re.compile(r"(?<!\{)\{\$([^{}]+?)\}(?!\})")


def repair_text(text: str) -> str:
    previous = None
    current = text
    while previous != current:
        previous = current
        current = SINGLE_BRACE_EXPR.sub(r"{{$\1}}", current)
    return current


def main() -> None:
    changed = []
    for path in sorted(WORKFLOWS.glob("*.json")):
        original = path.read_text()
        repaired = repair_text(original)
        if repaired != original:
            path.write_text(repaired)
            changed.append(str(path))
    if changed:
        print("Repaired generated n8n expressions in:")
        for item in changed:
            print(f"- {item}")
    else:
        print("No generated n8n expression repairs needed.")


if __name__ == "__main__":
    main()
