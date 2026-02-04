"""Pydantic models for RAG chunks and metadata."""

from datetime import datetime

from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    """Metadata associated with a chunk."""

    project_id: str
    source_type: str
    source_id: str
    chunk_index: int
    author: str | None = None
    date: datetime | None = None
    subject: str | None = None
    thread_context: str | None = None


class Chunk(BaseModel):
    """A text chunk with optional embedding and metadata."""

    id: str
    text: str
    embedding: list[float] | None = None
    metadata: ChunkMetadata
