"""threadwise: Thread-aware email ingestion for RAG systems."""

from threadwise.core import (
    AttachmentMetadata,
    Chunk,
    ChunkMetadata,
    EmailMessage,
    EmailThread,
    EmbeddingProvider,
    LLMProvider,
    ProcessedMessage,
    ProcessedThread,
)
from threadwise.embedding import Embedder, EmbeddingConfig, EmbeddingError
from threadwise.gmail import GmailClient
from threadwise.processing import (
    ChunkingConfig,
    EmailProcessor,
    ProcessingConfig,
    SummarizationConfig,
    ThreadChunker,
    ThreadSummarizer,
)

__version__ = "0.1.0"
__all__ = [
    "AttachmentMetadata",
    "Chunk",
    "ChunkMetadata",
    "ChunkingConfig",
    "Embedder",
    "EmbeddingConfig",
    "EmbeddingError",
    "EmailMessage",
    "EmailProcessor",
    "EmailThread",
    "EmbeddingProvider",
    "GmailClient",
    "LLMProvider",
    "ProcessedMessage",
    "ProcessedThread",
    "ProcessingConfig",
    "SummarizationConfig",
    "ThreadChunker",
    "ThreadSummarizer",
    "__version__",
]
