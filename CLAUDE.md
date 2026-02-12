# threadwise

Thread-aware email ingestion library for RAG systems. Python 3.12, uv, pgvector.

## Quick Reference

- `uv run pytest` - run tests
- `uv run pytest tests/ -m storage` - storage tests (requires docker compose up)  
- `uv run ruff check .` - lint
- `uv run mypy src` - type check
- `uv run ruff check . && uv run mypy src && uv run pytest` - full verification

## Project Structure

- `src/threadwise/` - library source (5 layers: ingestion, processing, embedding, storage, retrieval)
- `tests/` - pytest suite with fixtures in `tests/fixtures/`
- `tests/conftest.py` - shared fixtures, mock providers

## Architecture Context

Read these files when working on related areas:

- `README.md` - full architecture overview, design decisions, configuration reference
- `src/threadwise/core/models.py` - all Pydantic data models (Chunk, EmailThread, EmailMessage, Settings)
- `src/threadwise/core/protocols.py` - EmbeddingProvider and LLMProvider interfaces

## Code Style

- Type hints on everything (strict mypy)
- Pydantic v2 for all models and config
- Use `|` union syntax, not Optional
- Docstrings on public APIs only
- Tests: one assertion concept per test, descriptive names (`test_<what>_<condition>_<expected>`)

## Rules

- Never add default embedding or LLM providers. The library requires explicit configuration.
- Storage is pgvector only. No storage abstraction layer.
- Gmail only. No generic email abstraction.
- All external provider calls must go through the Protocol interfaces.
- Run full verification (ruff + mypy + pytest) after completing any task.
- Do not commit.
- Run full verification (ruff + mypy + pytest) after completing any task.

## Current Milestone

Check `.claude/docs/ROADMAP.md` for current milestone status and task details.