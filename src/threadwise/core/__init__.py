"""Core models and protocols for threadwise."""

from threadwise.core.models import (
    AttachmentMetadata,
    Chunk,
    ChunkMetadata,
    EmailMessage,
    EmailThread,
    ProcessedMessage,
    ProcessedThread,
)
from threadwise.core.protocols import EmbeddingProvider, LLMProvider

__all__ = [
    "AttachmentMetadata",
    "Chunk",
    "ChunkMetadata",
    "EmailMessage",
    "EmailThread",
    "EmbeddingProvider",
    "LLMProvider",
    "ProcessedMessage",
    "ProcessedThread",
]
