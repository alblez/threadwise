"""Tests for ThreadSummarizer."""

from datetime import datetime

import pytest
from pydantic import ValidationError

from tests.conftest import MockLLMProvider
from threadwise.core.models import ProcessedMessage, ProcessedThread
from threadwise.processing.config import SummarizationConfig
from threadwise.processing.summarizer import ThreadSummarizer


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


class TestLLMSummary:
    def test_llm_summary_calls_provider(self) -> None:
        """LLM provider generate() is called exactly once."""
        provider = MockLLMProvider()
        config = SummarizationConfig(method="llm", llm_provider=provider)
        summarizer = ThreadSummarizer(config)
        msg = _make_message("Hello, let's discuss the budget.")
        thread = _make_thread([msg])

        summarizer.summarize_thread(thread, "proj1")

        assert provider.call_count == 1

    def test_llm_summary_prompt_contains_messages(self) -> None:
        """The prompt sent to the provider includes message content."""
        provider = MockLLMProvider()
        config = SummarizationConfig(method="llm", llm_provider=provider)
        summarizer = ThreadSummarizer(config)
        msg = _make_message("We need to approve the Q3 budget.")
        thread = _make_thread([msg])

        summarizer.summarize_thread(thread, "proj1")

        assert "We need to approve the Q3 budget." in provider.last_prompt  # type: ignore[operator]

    def test_llm_summary_prompt_contains_template(self) -> None:
        """The prompt includes the summarization instruction template."""
        provider = MockLLMProvider()
        config = SummarizationConfig(method="llm", llm_provider=provider)
        summarizer = ThreadSummarizer(config)
        msg = _make_message("Budget discussion.")
        thread = _make_thread([msg])

        summarizer.summarize_thread(thread, "proj1")

        assert "Summarize the following email thread" in provider.last_prompt  # type: ignore[operator]

    def test_llm_summary_returns_provider_response(self) -> None:
        """The summary chunk text matches the provider response."""
        provider = MockLLMProvider(response="Summary of thread.")
        config = SummarizationConfig(method="llm", llm_provider=provider)
        summarizer = ThreadSummarizer(config)
        msg = _make_message("Content here.")
        thread = _make_thread([msg])

        chunk = summarizer.summarize_thread(thread, "proj1")

        assert chunk.text == "Summary of thread."

    def test_llm_summary_chunk_metadata(self) -> None:
        """Summary chunk has correct metadata fields."""
        provider = MockLLMProvider()
        config = SummarizationConfig(method="llm", llm_provider=provider)
        summarizer = ThreadSummarizer(config)
        msg = _make_message(
            "Content.",
            sender="Alice <alice@test.com>",
            date=datetime(2024, 3, 10, 9, 0),
        )
        thread = _make_thread([msg], thread_id="t42", subject="Q3 Budget")

        chunk = summarizer.summarize_thread(thread, "proj1")

        assert chunk.metadata.chunk_level == "summary"
        assert chunk.metadata.chunk_index == -1
        assert chunk.metadata.project_id == "proj1"
        assert chunk.metadata.source_type == "gmail"
        assert chunk.metadata.author == "Alice <alice@test.com>"
        assert chunk.metadata.date == datetime(2024, 3, 10, 9, 0)
        assert chunk.metadata.thread_context is None

    def test_llm_summary_truncates_long_thread(self) -> None:
        """Thread exceeding context_window triggers truncation, keeps recent messages."""
        provider = MockLLMProvider()
        # Small context window to force truncation (budget = 600 - 50 - 500 = 50 tokens)
        config = SummarizationConfig(
            method="llm",
            llm_provider=provider,
            context_window=600,
            max_summary_tokens=50,
        )
        summarizer = ThreadSummarizer(config)
        msgs = [
            _make_message(
                f"Message {i} with some content to use tokens.",
                message_id=f"m{i}",
                sender=f"User{i} <u{i}@test.com>",
            )
            for i in range(10)
        ]
        thread = _make_thread(msgs)

        summarizer.summarize_thread(thread, "proj1")

        assert "[Earlier messages truncated]" in provider.last_prompt  # type: ignore[operator]
        # Should keep the last message
        assert "Message 9" in provider.last_prompt  # type: ignore[operator]


class TestExtractiveSummary:
    def test_extractive_summary_uses_first_and_last(self) -> None:
        """Extractive summary contains text from both first and last messages."""
        config = SummarizationConfig(method="extractive")
        summarizer = ThreadSummarizer(config)
        msgs = [
            _make_message("Opening remarks about the project.", message_id="m1"),
            _make_message("Middle discussion.", message_id="m2"),
            _make_message("Final conclusions and next steps.", message_id="m3"),
        ]
        thread = _make_thread(msgs)

        chunk = summarizer.summarize_thread(thread, "proj1")

        assert "Opening remarks" in chunk.text
        assert "Final conclusions" in chunk.text

    def test_extractive_summary_single_message(self) -> None:
        """Extractive summary works with a single message."""
        config = SummarizationConfig(method="extractive")
        summarizer = ThreadSummarizer(config)
        msg = _make_message("Only message in the thread.")
        thread = _make_thread([msg])

        chunk = summarizer.summarize_thread(thread, "proj1")

        assert "Only message in the thread." in chunk.text

    def test_extractive_summary_no_llm_required(self) -> None:
        """Extractive config validates without an llm_provider."""
        config = SummarizationConfig(method="extractive")
        assert config.llm_provider is None


class TestSummarizationConfig:
    def test_llm_method_requires_provider(self) -> None:
        """ValidationError raised when method='llm' and no provider given."""
        with pytest.raises(ValidationError, match="llm_provider"):
            SummarizationConfig(method="llm")

    def test_summary_chunk_id_format(self) -> None:
        """Summary chunk id is '{thread_id}:summary'."""
        provider = MockLLMProvider()
        config = SummarizationConfig(method="llm", llm_provider=provider)
        summarizer = ThreadSummarizer(config)
        msg = _make_message("Content.")
        thread = _make_thread([msg], thread_id="abc123")

        chunk = summarizer.summarize_thread(thread, "proj1")

        assert chunk.id == "abc123:summary"
