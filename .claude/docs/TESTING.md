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

- `uv run pytest` - all tests except storage
- `uv run pytest -m storage` - storage tests (requires: docker compose up -d)
- `uv run pytest tests/test_models.py -v` - verbose single module
- `uv run pytest -k "thread"` - keyword filter

## Adding Fixtures

Place JSON files in tests/fixtures/. Name them descriptively:

- gmail_thread_simple.json - single message thread
- gmail_thread_reply_chain.json - 3+ message reply chain with HTML
- gmail_thread_attachments.json - thread with attachment metadata

## Docker Compose (M6+)

docker-compose.yml provides PostgreSQL 16 with pgvector extension on port 5433 (non-default to avoid conflicts).
