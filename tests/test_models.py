"""Tests for core models."""

from datetime import UTC, datetime

from rag_etl import Chunk, ChunkMetadata


def test_chunk_instantiation() -> None:
    """Test that a Chunk can be instantiated with required fields."""
    metadata = ChunkMetadata(
        project_id="proj-123",
        source_type="gmail",
        source_id="thread-abc",
        chunk_index=0,
        author="alice@example.com",
        date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        subject="Project Update",
    )

    chunk = Chunk(
        id="chunk-001",
        text="This is the chunk content.",
        metadata=metadata,
    )

    assert chunk.id == "chunk-001"
    assert chunk.text == "This is the chunk content."
    assert chunk.embedding is None
    assert chunk.metadata.project_id == "proj-123"
    assert chunk.metadata.source_type == "gmail"
    assert chunk.metadata.source_id == "thread-abc"
    assert chunk.metadata.chunk_index == 0
    assert chunk.metadata.author == "alice@example.com"
    assert chunk.metadata.subject == "Project Update"
    assert chunk.metadata.thread_context is None
