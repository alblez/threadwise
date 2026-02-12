#!/usr/bin/env bash
set -euo pipefail

# Read JSON from stdin (Claude Code pipes hook context via stdin, not $1)
INPUT=$(cat)
FILE=$(echo "$INPUT" | python3 -c "import json,sys; print(json.load(sys.stdin).get('tool_input',{}).get('file_path',''))")

# Skip non-Python files
[[ "$FILE" != *.py ]] && exit 0

# Run linter and type checker (|| true so we don't block, just report)
uv run ruff check "$FILE" 2>&1 || true
uv run mypy "$FILE" 2>&1 || true
exit 0