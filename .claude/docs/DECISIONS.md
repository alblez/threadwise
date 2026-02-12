# Architecture Decisions

| Decision | Choice | Reasoning |
| ---------- | -------- | ----------- |
| Retrieval strategy | Hierarchical (summary then detail) | Prevents thread noise from flooding LLM context |
| Pipeline composability | Independent layers, shared via data models | Each layer accepts and returns Pydantic models |
| Provider defaults | None (require explicit config) | Avoids coupling to any single AI provider |
| Storage backend | pgvector only | Single-backend focus avoids premature abstraction |
| Tokenizer | Configurable with cl100k_base fallback | Different models use different tokenizers |
| Email scope | Gmail only | Gmail API has specific structures worth optimizing for |
| Attachment handling | Metadata only | Content extraction is a separate problem domain |
| Thread summaries | LLM-generated with extractive fallback | LLM summaries are higher quality, fallback allows operation without LLM during ingestion |
