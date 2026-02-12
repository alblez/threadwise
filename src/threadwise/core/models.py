"""Pydantic models for email threads, RAG chunks, and metadata."""

from datetime import datetime

from pydantic import BaseModel


class ChunkMetadata(BaseModel):
    """Metadata associated with a chunk."""

    project_id: str
    source_type: str
    source_id: str
    chunk_index: int
    chunk_level: str = "detail"
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


class AttachmentMetadata(BaseModel):
    """Metadata for an email attachment."""

    filename: str
    mime_type: str
    size: int


class EmailMessage(BaseModel):
    """A single email message from Gmail."""

    message_id: str
    thread_id: str
    sender: str
    recipients: list[str]
    date: datetime
    subject: str | None = None
    body_html: str | None = None
    body_text: str | None = None
    in_reply_to: str | None = None
    attachments: list[AttachmentMetadata] = []


class EmailThread(BaseModel):
    """A Gmail thread containing ordered messages."""

    thread_id: str
    messages: list[EmailMessage]
    subject: str | None = None
