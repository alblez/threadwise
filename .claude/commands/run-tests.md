---
description: Run tests and report only failures
context: fork
agent: Explore
allowed-tools: Bash(uv run *)
argument-hint: "[pytest args, e.g. -m storage, -k thread, tests/test_models.py]"
---

# Run Tests

Run `uv run pytest --timeout=10 -q --tb=short --no-header $ARGUMENTS 2>&1 | tail -40` in the project root.

If no arguments are provided, run all tests: `uv run pytest --timeout=10 -q --tb=short --no-header 2>&1 | tail -40`.

If all tests pass, respond with only:
"All [N] tests passed."

If any tests fail, respond with:

- Number of passed/failed
- For each failure: test name, assertion error, and the relevant 3 lines of traceback
- Nothing else

If pytest fails to collect tests (import errors, fixture errors, syntax errors), return the error output verbatim with no analysis.

Your entire response must fit within 15 lines of plain text.

## Do Not

- Do not add any preamble, greeting, or introductory text.
- Do not add any commentary, suggestions, or analysis after the results.
- Do not repeat passing test names.
- Do not explain what the errors mean.
