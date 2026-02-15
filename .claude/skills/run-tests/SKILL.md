---
name: run-tests
description: Run tests and report only failures
context: fork
agent: Explore
allowed-tools: Bash(uv run *)
argument-hint: "[pytest args, e.g. -m storage, -k thread, tests/test_models.py]"
---

# Run Tests

Run this command in the project root:

```bash
timeout 30 uv run pytest -q --tb=short --no-header --timeout=10 -W ignore::DeprecationWarning $ARGUMENTS 2>&1 | tail -50
```

If no arguments are provided, run all tests:

```bash
timeout 30 uv run pytest -q --tb=short --no-header --timeout=10 -W ignore::DeprecationWarning 2>&1 | tail -50
```

Check the exit code after execution. Shape your response according to the matching case below.

## Case 1: All tests pass (exit code 0)

Respond with exactly one line:

```text
All [N] tests passed.
```

## Case 2: Test failures (exit code 1, five or fewer failures)

Respond with:

- Line 1: `[P] passed, [F] failed.`
- For each failure: test name, the assertion line, and one line of context above and below (3 lines per failure)

Maximum response length: 15 lines.

## Case 3: Mass failures (exit code 1, more than five failures)

Respond with:

- Line 1: `[P] passed, [F] failed.`
- For each failure: test name and the assertion line only (1 line per failure)
- Final line: `Run failing tests individually for full traceback.`

Maximum response length: 20 lines.

## Case 4: Timeout (exit code 124)

Respond with exactly one line:

```text
Tests timed out after 30s. A test may contain an infinite loop or blocking call.
```

## Case 5: Collection error (exit code 2)

Return the pytest output verbatim. Add nothing.

## Do Not

- Add preamble, greeting, or introductory text.
- Add commentary, suggestions, or analysis after the results.
- Repeat passing test names.
- Explain what the errors mean.
- Suggest fixes.
- Mention the timeout duration unless a timeout occurred.
- Rephrase or summarize collection errors.

Your entire response is plain text with no markdown formatting.
