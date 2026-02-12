# threadwise Roadmap

## Current Milestone: M1 - Gmail Ingestion

### Status: Not Started

### Goal
Gmail client class wrapping google-api-python-client that fetches threads
and returns structured EmailThread/EmailMessage objects.

### Tasks
- [ ] Gmail client class accepting caller-provided credentials
- [ ] Fetch thread by ID, returning EmailThread
- [ ] Fetch threads by label/query
- [ ] Mock fixtures with realistic multi-message threads
- [ ] Full test coverage against mocks

### Milestone Overview

| Milestone | Description | Status |
|-----------|-------------|--------|
| M0 | Re-foundation: rename, models, protocols | ✅ Complete |
| M1 | Gmail ingestion with mock data | 🔲 Current |
| M2 | Email processing (HTML to markdown, cleaning) | 🔲 Planned |
| M3 | Smart thread-aware chunking | 🔲 Planned |
| M4 | Thread summarization (LLM + extractive fallback) | 🔲 Planned |
| M5 | Embedding with batching and rate limiting | 🔲 Planned |
| M6 | pgvector storage (schema, upsert, indexing) | 🔲 Planned |
| M7 | Hierarchical retrieval engine | 🔲 Planned |
| M8 | Pipeline orchestrator and Settings | 🔲 Planned |
| M9 | Hardening (logging, retries, error handling) | 🔲 Planned |
