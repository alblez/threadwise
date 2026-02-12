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
from threadwise.gmail import GmailClient
from threadwise.processing import EmailProcessor, ProcessingConfig

__version__ = "0.1.0"
__all__ = [
    "AttachmentMetadata",
    "Chunk",
    "ChunkMetadata",
    "EmailMessage",
    "EmailProcessor",
    "EmailThread",
    "EmbeddingProvider",
    "GmailClient",
    "LLMProvider",
    "ProcessedMessage",
    "ProcessedThread",
    "ProcessingConfig",
    "__version__",
]
