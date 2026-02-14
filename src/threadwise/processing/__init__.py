"""Email processing pipeline for threadwise."""

from threadwise.processing.chunker import ThreadChunker
from threadwise.processing.config import ChunkingConfig, ProcessingConfig, SummarizationConfig
from threadwise.processing.email_processor import EmailProcessor
from threadwise.processing.summarizer import ThreadSummarizer

__all__ = [
    "ChunkingConfig",
    "EmailProcessor",
    "ProcessingConfig",
    "SummarizationConfig",
    "ThreadChunker",
    "ThreadSummarizer",
]
