"""threadwise: Thread-aware email ingestion for RAG systems."""

from threadwise.core import (
    AttachmentMetadata,
    Chunk,
    ChunkMetadata,
    EmailMessage,
    EmailThread,
    EmbeddingProvider,
    LLMProvider,
)

__version__ = "0.1.0"
__all__ = [
    "AttachmentMetadata",
    "Chunk",
    "ChunkMetadata",
    "EmailMessage",
    "EmailThread",
    "EmbeddingProvider",
    "LLMProvider",
    "__version__",
]
