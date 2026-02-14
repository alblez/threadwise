"""Tests for ThreadChunker."""

from datetime import datetime

from threadwise.core.models import ProcessedMessage, ProcessedThread
from threadwise.processing.chunker import ThreadChunker
from threadwise.processing.config import ChunkingConfig


def _make_message(
    content: str,
    sender: str = "Alice <alice@test.com>",
    date: datetime | None = None,
    message_id: str = "msg1",
    thread_id: str = "thread1",
) -> ProcessedMessage:
    return ProcessedMessage(
        message_id=message_id,
        thread_id=thread_id,
        sender=sender,
        recipients=["bob@test.com"],
        date=date or datetime(2024, 1, 15, 10, 0),
        subject="Test Subject",
        content=content,
    )


def _make_thread(
    messages: list[ProcessedMessage],
    thread_id: str = "thread1",
    subject: str = "Test Subject",
) -> ProcessedThread:
    return ProcessedThread(thread_id=thread_id, messages=messages, subject=subject)


class TestThreadChunker:
    def test_short_thread_single_chunk(self) -> None:
        """3 short messages → 1 chunk."""
        msgs = [
            _make_message("Hello there.", sender="Alice <a@t.com>", message_id="m1"),
            _make_message("Hi Alice!", sender="Bob <b@t.com>", message_id="m2"),
            _make_message("How are you?", sender="Alice <a@t.com>", message_id="m3"),
        ]
        thread = _make_thread(msgs)
        chunker = ThreadChunker(ChunkingConfig(chunk_size=512))
        chunks = chunker.chunk_thread(thread, "proj1")

        assert len(chunks) == 1

    def test_short_thread_metadata_correct(self) -> None:
        """Single chunk has correct metadata fields."""
        msg = _make_message("Short content.", sender="Alice <a@t.com>")
        thread = _make_thread([msg])
        chunker = ThreadChunker()
        chunks = chunker.chunk_thread(thread, "proj1")

        assert len(chunks) == 1
        c = chunks[0]
        assert c.metadata.project_id == "proj1"
        assert c.metadata.source_type == "gmail"
        assert c.metadata.source_id == "thread1"
        assert c.metadata.chunk_index == 0
        assert c.metadata.thread_context is None
        assert c.metadata.subject == "Test Subject"
        assert c.metadata.chunk_level == "detail"

    def test_long_thread_splits_at_message_boundaries(self) -> None:
        """Messages split at boundaries, no mid-message split."""
        msgs = [
            _make_message(
                f"Message {i} content with some words to use tokens.",
                message_id=f"m{i}",
                sender=f"User{i} <u{i}@t.com>",
            )
            for i in range(5)
        ]
        thread = _make_thread(msgs)
        # Use a small chunk_size so not all messages fit in one chunk
        chunker = ThreadChunker(ChunkingConfig(chunk_size=60))
        chunks = chunker.chunk_thread(thread, "proj1")

        assert len(chunks) >= 2
        # Each chunk text should contain complete message headers
        for chunk in chunks:
            assert "**From:" in chunk.text

    def test_chunk_overlap_not_applied_at_message_boundaries(self) -> None:
        """Message boundary splits don't add overlap text."""
        msgs = [
            _make_message("First message content here.", message_id="m1", sender="A <a@t.com>"),
            _make_message("Second message content here.", message_id="m2", sender="B <b@t.com>"),
        ]
        thread = _make_thread(msgs)
        chunker = ThreadChunker(ChunkingConfig(chunk_size=30, chunk_overlap=10))
        chunks = chunker.chunk_thread(thread, "proj1")

        if len(chunks) >= 2:
            # Second chunk should not start with content from the first chunk's message
            assert "First message" not in chunks[1].text

    def test_oversized_message_splits_at_paragraphs(self) -> None:
        """A single large message splits at paragraph boundaries."""
        paragraphs = [
            "This is the first paragraph with enough words to take up tokens.",
            "This is the second paragraph also with enough words for tokens.",
            "This is the third paragraph with additional words for token count.",
        ]
        content = "\n\n".join(paragraphs)
        msg = _make_message(content, sender="Alice <a@t.com>")
        thread = _make_thread([msg])
        chunker = ThreadChunker(ChunkingConfig(chunk_size=40, chunk_overlap=5))
        chunks = chunker.chunk_thread(thread, "proj1")

        assert len(chunks) >= 2

    def test_thread_context_populated_for_later_chunks(self) -> None:
        """Second chunk has thread_context referencing earlier messages."""
        msgs = [
            _make_message(
                "First message with enough content to fill space.",
                message_id="m1",
                sender="Alice <a@t.com>",
                date=datetime(2024, 1, 15, 10, 0),
            ),
            _make_message(
                "Second message also with enough content to fill space.",
                message_id="m2",
                sender="Bob <b@t.com>",
                date=datetime(2024, 1, 15, 11, 0),
            ),
        ]
        thread = _make_thread(msgs)
        chunker = ThreadChunker(ChunkingConfig(chunk_size=40))
        chunks = chunker.chunk_thread(thread, "proj1")

        assert len(chunks) >= 2
        assert chunks[0].metadata.thread_context is None
        later = chunks[-1]
        assert later.metadata.thread_context is not None
        assert "Preceding" in later.metadata.thread_context

    def test_thread_context_none_for_first_chunk(self) -> None:
        """First chunk always has thread_context=None."""
        msgs = [
            _make_message("Some content.", message_id="m1"),
            _make_message("More content.", message_id="m2"),
        ]
        thread = _make_thread(msgs)
        chunker = ThreadChunker()
        chunks = chunker.chunk_thread(thread, "proj1")

        assert chunks[0].metadata.thread_context is None

    def test_chunk_ids_sequential(self) -> None:
        """All chunks have sequential chunk_index 0, 1, 2..."""
        msgs = [
            _make_message(
                f"Message {i} with some words here.",
                message_id=f"m{i}",
                sender=f"User{i} <u{i}@t.com>",
            )
            for i in range(5)
        ]
        thread = _make_thread(msgs)
        chunker = ThreadChunker(ChunkingConfig(chunk_size=50))
        chunks = chunker.chunk_thread(thread, "proj1")

        for i, chunk in enumerate(chunks):
            assert chunk.metadata.chunk_index == i
            assert chunk.id == f"thread1:{i}"

    def test_author_from_first_message_in_chunk(self) -> None:
        """Each chunk's metadata.author = sender of first message in that chunk."""
        msgs = [
            _make_message(
                "Content from Alice with words.",
                message_id="m1",
                sender="Alice <a@t.com>",
            ),
            _make_message(
                "Content from Bob with words here.",
                message_id="m2",
                sender="Bob <b@t.com>",
            ),
        ]
        thread = _make_thread(msgs)
        chunker = ThreadChunker(ChunkingConfig(chunk_size=30))
        chunks = chunker.chunk_thread(thread, "proj1")

        if len(chunks) >= 2:
            assert chunks[0].metadata.author == "Alice <a@t.com>"
            assert chunks[1].metadata.author == "Bob <b@t.com>"

    def test_empty_thread_returns_empty_list(self) -> None:
        """No messages → empty list."""
        thread = _make_thread([])
        chunker = ThreadChunker()
        chunks = chunker.chunk_thread(thread, "proj1")

        assert chunks == []

    def test_custom_chunk_size_respected(self) -> None:
        """ChunkingConfig(chunk_size=256) → smaller chunks than default."""
        content = " ".join(["word"] * 200)
        msg = _make_message(content, sender="Alice <a@t.com>")
        thread = _make_thread([msg])

        chunker_small = ThreadChunker(ChunkingConfig(chunk_size=50))
        chunker_large = ThreadChunker(ChunkingConfig(chunk_size=512))

        small_chunks = chunker_small.chunk_thread(thread, "proj1")
        large_chunks = chunker_large.chunk_thread(thread, "proj1")

        assert len(small_chunks) > len(large_chunks)

    def test_message_headers_included_in_text(self) -> None:
        """Chunk text contains **From: ... header lines."""
        msg = _make_message(
            "Hello world.",
            sender="Alice <a@t.com>",
            date=datetime(2024, 1, 15, 10, 30),
        )
        thread = _make_thread([msg])
        chunker = ThreadChunker()
        chunks = chunker.chunk_thread(thread, "proj1")

        assert "**From: Alice <a@t.com> (2024-01-15 10:30)**" in chunks[0].text
