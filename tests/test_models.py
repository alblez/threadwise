"""Tests for core models."""

from datetime import UTC, datetime

from threadwise import (
    AttachmentMetadata,
    Chunk,
    ChunkMetadata,
    EmailMessage,
    EmailThread,
)


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


def test_chunk_metadata_chunk_level_defaults_to_detail() -> None:
    metadata = ChunkMetadata(
        project_id="proj-123",
        source_type="gmail",
        source_id="thread-abc",
        chunk_index=0,
    )

    assert metadata.chunk_level == "detail"


def test_chunk_metadata_chunk_level_accepts_summary() -> None:
    metadata = ChunkMetadata(
        project_id="proj-123",
        source_type="gmail",
        source_id="thread-abc",
        chunk_index=0,
        chunk_level="summary",
    )

    assert metadata.chunk_level == "summary"


def test_attachment_metadata_instantiation() -> None:
    attachment = AttachmentMetadata(
        filename="report.pdf",
        mime_type="application/pdf",
        size=1024,
    )

    assert attachment.filename == "report.pdf"
    assert attachment.mime_type == "application/pdf"
    assert attachment.size == 1024


def test_email_message_instantiation() -> None:
    msg = EmailMessage(
        message_id="msg-001",
        thread_id="thread-abc",
        sender="alice@example.com",
        recipients=["bob@example.com", "carol@example.com"],
        date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        subject="Project Update",
        body_html="<p>Hello</p>",
        body_text="Hello",
    )

    assert msg.message_id == "msg-001"
    assert msg.thread_id == "thread-abc"
    assert msg.sender == "alice@example.com"
    assert msg.recipients == ["bob@example.com", "carol@example.com"]
    assert msg.subject == "Project Update"
    assert msg.body_html == "<p>Hello</p>"
    assert msg.body_text == "Hello"
    assert msg.in_reply_to is None
    assert msg.attachments == []


def test_email_message_with_attachments() -> None:
    attachment = AttachmentMetadata(
        filename="report.pdf",
        mime_type="application/pdf",
        size=2048,
    )
    msg = EmailMessage(
        message_id="msg-002",
        thread_id="thread-abc",
        sender="alice@example.com",
        recipients=["bob@example.com"],
        date=datetime(2024, 1, 15, 10, 30, tzinfo=UTC),
        attachments=[attachment],
    )

    assert len(msg.attachments) == 1
    assert msg.attachments[0].filename == "report.pdf"


def test_email_thread_with_multiple_messages() -> None:
    msg1 = EmailMessage(
        message_id="msg-001",
        thread_id="thread-abc",
        sender="alice@example.com",
        recipients=["bob@example.com"],
        date=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        subject="Project Update",
        body_text="Initial message.",
    )
    msg2 = EmailMessage(
        message_id="msg-002",
        thread_id="thread-abc",
        sender="bob@example.com",
        recipients=["alice@example.com"],
        date=datetime(2024, 1, 15, 11, 0, tzinfo=UTC),
        subject="Re: Project Update",
        body_text="Got it, thanks.",
        in_reply_to="msg-001",
    )

    thread = EmailThread(
        thread_id="thread-abc",
        messages=[msg1, msg2],
        subject="Project Update",
    )

    assert thread.thread_id == "thread-abc"
    assert len(thread.messages) == 2
    assert thread.messages[0].sender == "alice@example.com"
    assert thread.messages[1].in_reply_to == "msg-001"
    assert thread.subject == "Project Update"


def test_embedding_provider_is_structural_protocol() -> None:
    from threadwise import EmbeddingProvider

    class MyEmbedder:
        def embed(self, texts: list[str]) -> list[list[float]]:
            return [[0.1] * 3 for _ in texts]

    embedder = MyEmbedder()
    assert isinstance(embedder, EmbeddingProvider)


def test_llm_provider_is_structural_protocol() -> None:
    from threadwise import LLMProvider

    class MyLLM:
        def generate(self, prompt: str) -> str:
            return "response"

    llm = MyLLM()
    assert isinstance(llm, LLMProvider)
