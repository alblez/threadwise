# threadwise Roadmap

## Current Milestone: M6 - pgvector Storage

### Status: Not Started

### Completed: M5 - Embedding Layer

- [x] New `src/threadwise/embedding/` package
- [x] `EmbeddingConfig` model with provider, model, dimensions, and retry settings
- [x] `Embedder` class with `embed_texts()` and `embed_chunks()` supporting batching
- [x] Exponential backoff with jitter for rate-limit errors
- [x] `EmbeddingError` with batch tracking
- [x] 11 new tests covering batching and error handling

### Completed: M4 - Thread Summarization

- [x] `ThreadSummarizer` class generating single summary chunk per thread
- [x] `SummarizationConfig` with LLM and extractive method support
- [x] LLM-based summarization with token-aware truncation (cl100k_base)
- [x] Extractive fallback (first/last paragraph heuristic)
- [x] Summary chunk structure with specialized metadata (chunk_level="summary")
- [x] 18 tests covering truncation and summarization methods

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
| M4 | Thread summarization (LLM + extractive fallback) | ✅ Complete |
| M5 | Embedding with batching and rate limiting | ✅ Complete |
| M6 | pgvector storage (schema, upsert, indexing) | 🔲 Current |
| M7 | Hierarchical retrieval engine | 🔲 Planned |
| M8 | Pipeline orchestrator and Settings | 🔲 Planned |
| M9 | Hardening (logging, retries, error handling) | 🔲 Planned |
