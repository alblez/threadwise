---
description: Run tests and report only failures
context: fork
agent: Explore
allowed-tools: Bash(uv run *)
argument-hint: "[pytest args, e.g. -m storage, -k thread, tests/test_models.py]"
---

# Run Tests

Run `uv run pytest -v $ARGUMENTS` in the project root.

If no arguments are provided, run all tests: `uv run pytest -v`.

If all tests pass, respond with only:
"All [N] tests passed."

If any tests fail, respond with:

- Number of passed/failed
- For each failure: test name, assertion error, and the relevant 5 lines of traceback
- Nothing else
