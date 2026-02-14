"""Email processing pipeline for threadwise."""

from threadwise.processing.chunker import ThreadChunker
from threadwise.processing.config import ChunkingConfig, ProcessingConfig
from threadwise.processing.email_processor import EmailProcessor

__all__ = ["ChunkingConfig", "EmailProcessor", "ProcessingConfig", "ThreadChunker"]
