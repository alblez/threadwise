# threadwise

**Thread-aware email ingestion for RAG systems.**

![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue.svg)
![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)

---

## The Problem

Email is one of the richest data sources inside any organization, and one of the hardest to make searchable with AI. Existing tools like LangChain's Gmail loader and LlamaIndex's GmailReader handle basic ingestion but break down on the realities of email data:

**Thread context gets destroyed.** Naive chunking splits a 15-message reply chain into isolated fragments. The chunk containing "Yes, approved" loses all meaning without the preceding discussion. Vector search returns the fragment, and the LLM hallucinates the rest.

**Noise overwhelms signal.** Email threads are full of signatures, legal disclaimers, quoted reply blocks, tracking pixels, and "Thanks!" messages. Generic loaders embed all of it, polluting your vector space. A query about "Q3 budget approval" returns chunks dominated by boilerplate HTML and Outlook formatting artifacts.

**Metadata gets stripped.** Who sent the message, when, which thread it belongs to, whether it was a reply or a forward. Generic loaders flatten this into plain text and lose the structure that makes email data queryable. You can't filter "emails from John about the budget in October" without rich metadata.

## How threadwise Solves It

threadwise is a Python library that treats email structure as a first-class concern. Three ideas make it different from generic ingestion tools.

### Email-Specific Processing

Before any embedding happens, threadwise cleans email content the way a human would. HTML gets converted to clean markdown. Signatures are detected and stripped. Quoted reply blocks are collapsed so the same paragraph doesn't appear five times across a thread. Tracking pixels and invisible formatting artifacts are removed. What remains is the actual content people wrote.

### Hierarchical Indexing

threadwise stores two layers of content per thread. First, a **summary chunk** that captures the essence of the conversation (generated via LLM or extractive fallback). Second, **detail chunks** containing the actual message content, segmented with awareness of message boundaries and reply context.

During retrieval, summaries are searched first. Only threads whose summaries match the query get their detail chunks retrieved. This prevents a 50-message reply-all chain from flooding the LLM context window when only the final conclusion was relevant.

### Metadata Pre-Filtering

Every chunk carries structured metadata: project ID, sender, date, subject, thread relationships, chunk level (summary vs. detail). Queries filter on metadata *before* vector search, reducing the search space and improving precision. "What did John say about the budget?" becomes a metadata filter (`sender=John`, `topic=budget`) followed by a scoped vector search, rather than a brute-force semantic match across everything.

## Architecture

```text
┌─────────────────────────────────────────────────────┐
│                   Pipeline                          │
│              (Settings + orchestration)              │
└────┬────────┬──────────┬──────────┬────────┬────────┘
     │        │          │          │        │
     ▼        ▼          ▼          ▼        ▼
┌────────┐┌────────┐┌─────────┐┌────────┐┌──────────┐
│Ingest  ││Process ││Summarize││ Embed  ││ Store +  │
│        ││        ││         ││        ││ Retrieve │
│Gmail   ││HTML→MD ││LLM or   ││Batched ││pgvector  │
│API     ││Chunk   ││Extract  ││Vectors ││Hybrid    │
│Client  ││Clean   ││         ││        ││Search    │
└────────┘└────────┘└─────────┘└────────┘└──────────┘
```

Each layer is independently usable. You can use the Gmail client and processor without touching pgvector. You can bring pre-chunked data and use just the storage and retrieval layers. The Pipeline class connects everything for the common case.

## Usage

```python
from threadwise import Pipeline, Settings
from threadwise.config import (
    EmbeddingConfig,
    GmailConfig,
    LLMConfig,
    StorageConfig,
)

# Bring your own providers
from your_app import MyEmbedder, MyLLM

settings = Settings(
    embedding=EmbeddingConfig(
        provider=MyEmbedder(),
        model="your-embedding-model",
        dimensions=1536,
    ),
    llm=LLMConfig(
        provider=MyLLM(),
        model="your-llm-model",
        context_window=128_000,
    ),
    storage=StorageConfig(dsn="postgresql://localhost:5432/threadwise"),
    gmail=GmailConfig(labels=["INBOX", "SENT"]),
)

pipeline = Pipeline(settings)

# Ingest Gmail threads into pgvector
pipeline.ingest(credentials=google_creds, project_id="nike-commercial-2026")

# Query with automatic hierarchical retrieval
results = pipeline.query(
    "What did John say about the budget?",
    project_id="nike-commercial-2026",
)

for result in results:
    print(f"[{result.metadata.author}, {result.metadata.date}]")
    print(result.text)
```

> **Note:** This is the aspirational API. It will evolve as each milestone is implemented.

## Configuration

threadwise requires explicit configuration for external providers. It ships with no built-in embedding model or LLM. You choose the providers, the library handles everything else with sensible defaults.

### Required Configuration

| Group | Field | Description |
| ------- | ------- | ------------- |
| `embedding` | `provider` | Callable or protocol implementation for embedding |
| `embedding` | `model` | Model identifier string |
| `embedding` | `dimensions` | Embedding vector dimensions |
| `llm` | `provider` | Callable or protocol implementation for LLM |
| `llm` | `model` | Model identifier string |
| `llm` | `context_window` | Context window size in tokens |
| `storage` | `dsn` | PostgreSQL connection string |

### Optional Configuration (with defaults)

| Group | Field | Default | Description |
| ------- | ------- | --------- | ------------- |
| `embedding` | `batch_size` | `100` | Vectors per API call |
| `llm` | `temperature` | `0.0` | LLM temperature for summarization |
| `llm` | `max_tokens` | `300` | Max output tokens for summaries |
| `storage` | `table_prefix` | `"threadwise"` | PostgreSQL table name prefix |
| `storage` | `index_type` | `"hnsw"` | pgvector index type |
| `processing` | `chunk_size` | `512` | Target chunk size in tokens |
| `processing` | `chunk_overlap` | `50` | Overlap between chunks in tokens |
| `processing` | `tokenizer` | `"cl100k_base"` | Tokenizer name or callable `(str) -> int` |
| `processing` | `strip_signatures` | `true` | Remove email signatures |
| `processing` | `quoted_text` | `"collapse"` | How to handle quoted replies |
| `retrieval` | `summary_top_k` | `10` | Summaries to retrieve per query |
| `retrieval` | `detail_top_k` | `5` | Detail chunks per matched thread |
| `retrieval` | `similarity_threshold` | `0.7` | Minimum cosine similarity |
| `retrieval` | `hierarchical` | `true` | Use two-layer search (false = flat) |
| `gmail` | `labels` | `["INBOX"]` | Gmail labels to fetch |
| `gmail` | `fetch_batch_size` | `50` | Threads per API call |

### Minimal Configuration Example

```python
Settings(
    embedding=EmbeddingConfig(
        provider=my_embedder,
        model="your-embedding-model",
        dimensions=1536,
    ),
    llm=LLMConfig(
        provider=my_llm,
        model="your-llm-model",
        context_window=128_000,
    ),
    storage=StorageConfig(dsn="postgresql://localhost/threadwise"),
)
```

Everything else inherits defaults.

## Roadmap

| Milestone | Description | Status |
| ----------- | ------------- | -------- |
| M0 | Re-foundation: rename, README, models, provider protocols | ✅ Complete |
| M1 | Gmail ingestion with mock data | ✅ Complete |
| M2 | Email processing (HTML→markdown, signature stripping, cleaning) | ✅ Complete |
| M3 | Smart thread-aware chunking | ✅ Complete |
| M4 | Thread summarization (LLM + extractive fallback) | ✅ Complete |
| M5 | Embedding with batching and rate limiting | ✅ Complete |
| M6 | pgvector storage (schema, upsert, indexing) | 🔲 Current |
| M7 | Hierarchical retrieval engine | 🔲 Planned |
| M8 | Pipeline orchestrator and Settings | 🔲 Planned |
| M9 | Hardening (logging, retries, error handling, progress) | 🔲 Planned |

## What threadwise Does NOT Do

Explicit boundaries to set expectations:

- **Does not handle OAuth.** The caller provides a `google.oauth2.credentials.Credentials` object. Token refresh, consent flows, and credential storage are your responsibility.
- **Does not extract attachment content.** Attachment metadata (filename, MIME type, size) is preserved. Downloading or parsing attachment files is out of scope.
- **Does not support storage backends other than pgvector.** The library is opinionated about PostgreSQL with the pgvector extension. There is no storage abstraction layer.
- **Does not support email sources other than Gmail.** The internal data models are shaped around Gmail's API. Outlook, IMAP, and other providers are not supported.
- **Does not ship with default providers.** You must explicitly configure an embedding provider and an LLM provider. The library makes no assumptions about which AI services you use.

## Development Setup

```bash
git clone https://github.com/your-org/threadwise.git
cd threadwise

# Install with dev dependencies
uv pip install -e ".[dev]"

# Run tests
uv run pytest

# Lint
uv run ruff check .

# Type check
uv run mypy src
```

### Running Storage Tests

Storage tests (M6+) require PostgreSQL with pgvector. Use Docker Compose:

```bash
docker compose up -d
uv run pytest tests/ -m storage
docker compose down
```

## Design Decisions

Key architectural choices and their reasoning, recorded for future reference.

| Decision | Choice | Reasoning |
| ---------- | -------- | ----------- |
| Retrieval strategy | Hierarchical (summary→detail) | Prevents thread noise from flooding LLM context. Inspired by LlamaIndex's recursive retrieval pattern. |
| Pipeline composability | Independent layers, shared via data models | Inspired by LangChain's composability, but without framework coupling. Each layer accepts and returns Pydantic models. |
| Provider defaults | None (require explicit config) | Avoids opinionated coupling to any single AI provider. Users bring their own embedding and LLM. |
| Storage backend | pgvector only | Single-backend focus avoids premature abstraction. Matches target use case (PostgreSQL-based applications). |
| Tokenizer | Configurable with `cl100k_base` fallback | Different models use different tokenizers. Hardcoding one would produce inaccurate chunk sizes for non-OpenAI models. |
| Email scope | Gmail only | Gmail API has specific structures (thread grouping, label system). Supporting multiple providers would require a generic email abstraction that sacrifices Gmail-specific features. |
| Attachment handling | Metadata only | Content extraction (PDF parsing, image OCR) is a separate problem domain. Including it would double the library's complexity and dependency tree. |
| Thread summaries | LLM-generated with extractive fallback | LLM summaries are higher quality. Extractive fallback (first/last message heuristic) allows the hierarchical storage structure to work without LLM dependency during ingestion. |