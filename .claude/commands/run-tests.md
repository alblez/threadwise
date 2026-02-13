---
description: Run tests and report only failures
context: fork
agent: Explore
allowed-tools: Bash(uv run *)
---

# Run Tests

Run `uv run pytest -v` in the project root.

If all tests pass, respond with only:
"All [N] tests passed."

If any tests fail, respond with:

- Number of passed/failed
- For each failure: test name, assertion error, and the relevant 5 lines of traceback
- Nothing else
