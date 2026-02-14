# threadwise Roadmap

## Current Milestone: M4 - Thread Summarization

### Status: Not Started

### Completed: M3 - Smart Thread-Aware Chunking

- [x] ChunkingConfig model (chunk_size, chunk_overlap, tokenizer, preserve_message_boundaries)
- [x] ThreadChunker class with message-boundary-aware splitting
- [x] Oversized message handling (paragraph → sentence → token boundary splits)
- [x] Thread context generation for later chunks
- [x] tiktoken-based token counting
- [x] 12 tests covering all chunking scenarios

### Completed: M2 - Email Processing

- [x] ProcessedMessage and ProcessedThread models
- [x] ProcessingConfig with signature/quoted text/tracking options
- [x] EmailProcessor: HTML to markdown conversion (markdownify)
- [x] Tracking pixel and invisible element removal
- [x] Signature stripping (delimiter, salutation, "Sent from" patterns)
- [x] Quoted reply handling (collapse/strip/keep)
- [x] Whitespace normalization
- [x] HTML email fixtures and 14 tests

### Completed: M1 - Gmail Ingestion

- [x] Gmail client class accepting caller-provided credentials
- [x] Fetch thread by ID, returning EmailThread
- [x] Fetch threads by label/query with pagination
- [x] Mock fixtures with realistic multi-message threads
- [x] Full test coverage against mocks (10 tests)

### Milestone Overview

| Milestone | Description | Status |
| ----------- | ------------- | -------- |
| M0 | Re-foundation: rename, models, protocols | ✅ Complete |
| M1 | Gmail ingestion with mock data | ✅ Complete |
| M2 | Email processing (HTML to markdown, cleaning) | ✅ Complete |
| M3 | Smart thread-aware chunking | ✅ Complete |
| M4 | Thread summarization (LLM + extractive fallback) | 🔲 Current |
| M5 | Embedding with batching and rate limiting | 🔲 Planned |
| M6 | pgvector storage (schema, upsert, indexing) | 🔲 Planned |
| M7 | Hierarchical retrieval engine | 🔲 Planned |
| M8 | Pipeline orchestrator and Settings | 🔲 Planned |
| M9 | Hardening (logging, retries, error handling) | 🔲 Planned |
