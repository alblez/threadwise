# Testing Strategy

## Principles

- All tests run without network access (mock external APIs)
- One assertion concept per test
- Descriptive names: `test_<what>_<condition>_<expected>`

## Mock Patterns

- Gmail API: mock google-api-python-client responses using JSON fixtures in tests/fixtures/
- Embedding provider: mock implementation returning deterministic vectors
- LLM provider: mock implementation returning canned responses
- pgvector: real PostgreSQL via docker-compose (tests marked with @pytest.mark.storage)

## Running Tests

Use the `/run-tests` command (runs in a sub-agent to save tokens):

- `/run-tests` - all tests except storage
- `/run-tests -m storage` - storage tests (requires: docker compose up -d)
- `/run-tests tests/test_models.py` - single module
- `/run-tests -k "thread"` - keyword filter

Raw pytest commands (for human use outside Claude Code):

- `uv run pytest` - all tests except storage
- `uv run pytest -m storage` - storage tests
- `uv run pytest tests/test_models.py -v` - verbose single module
- `uv run pytest -k "thread"` - keyword filter

## Adding Fixtures

Place JSON files in tests/fixtures/. Name them descriptively:

- gmail_thread_simple.json - single message thread
- gmail_thread_reply_chain.json - 3+ message reply chain with HTML
- gmail_thread_attachments.json - thread with attachment metadata

## Database Tests

Database tests require PostgreSQL 18.2 + pgvector 0.8.1 running via Docker.

### Starting the database

```bash
docker compose up -d
```

Wait for the healthcheck to pass (container reports "healthy").

### Running tests

```bash
# All tests (DB tests auto-skip if Docker is down)
uv run pytest

# Only non-DB tests
uv run pytest -m "not db"

# Only DB tests
uv run pytest -m db

# Smoke tests specifically
uv run pytest tests/test_docker_smoke.py -v
```

### Test isolation strategy

- **Default: transaction rollback.** Each test gets a `db_connection` fixture that rolls back on teardown. Tests never commit, so they leave no side effects.
- **Alternative: table truncation.** For tests that must commit (e.g., testing auto-commit behavior), use the `db_clean_tables` fixture which truncates all test tables before each test.

### Fixtures (in tests/conftest_db.py)

| Fixture | Scope | Purpose |
| ------- | ----- | ------- |
| `db_connection_string` | session | DSN string; skips session if DB unreachable |
| `db_connection` | function | Connection with rollback-on-teardown |
| `db_setup_tables` | session | Creates/drops test tables |
| `db_clean_tables` | function | Truncates test tables before each test |

### Stopping the database

```bash
docker compose down
```
