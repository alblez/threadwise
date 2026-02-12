"""Tests for the email processing pipeline."""

from datetime import UTC, datetime

from tests.fixtures.email_html import (
    GMAIL_REPLY_HTML,
    HTML_WITH_REGARDS_SIGNATURE,
    HTML_WITH_SIGNATURE,
    HTML_WITH_TRACKING,
    OUTLOOK_HTML,
    PLAIN_TEXT_WITH_SIGNATURE,
    SIMPLE_HTML,
)
from threadwise.core.models import EmailMessage, EmailThread, ProcessedThread
from threadwise.processing import EmailProcessor, ProcessingConfig


def _make_message(
    body_html: str | None = None,
    body_text: str | None = None,
    message_id: str = "msg-1",
    thread_id: str = "thread-1",
) -> EmailMessage:
    """Create an EmailMessage with minimal required fields."""
    return EmailMessage(
        message_id=message_id,
        thread_id=thread_id,
        sender="test@example.com",
        recipients=["recipient@example.com"],
        date=datetime(2024, 1, 15, 10, 0, tzinfo=UTC),
        subject="Test Subject",
        body_html=body_html,
        body_text=body_text,
    )


def _make_thread(messages: list[EmailMessage]) -> EmailThread:
    """Create an EmailThread from a list of messages."""
    return EmailThread(
        thread_id=messages[0].thread_id if messages else "thread-1",
        messages=messages,
        subject=messages[0].subject if messages else None,
    )


class TestHtmlToMarkdown:
    def test_simple_html_converts_to_markdown(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(SIMPLE_HTML, None)

        assert "[design document](https://example.com/doc)" in result
        assert "**deadline**" in result
        assert "<p>" not in result
        assert "<b>" not in result

    def test_outlook_html_strips_mso_noise(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(OUTLOOK_HTML, None)

        assert "quarterly results" in result
        assert "Revenue is up 15%" in result
        assert "MsoNormal" not in result
        assert "gte mso 9" not in result
        assert "<span" not in result


class TestQuotedText:
    def test_gmail_reply_quoted_text_collapsed(self) -> None:
        proc = EmailProcessor(ProcessingConfig(quoted_text="collapse"))
        result = proc._clean_content(GMAIL_REPLY_HTML, None)

        assert "I agree with the proposed timeline" in result
        assert "[Previous message quoted]" in result
        assert "project timeline for Q1" not in result

    def test_gmail_reply_quoted_text_stripped(self) -> None:
        proc = EmailProcessor(ProcessingConfig(quoted_text="strip"))
        result = proc._clean_content(GMAIL_REPLY_HTML, None)

        assert "I agree with the proposed timeline" in result
        assert "[Previous message quoted]" not in result
        assert "project timeline for Q1" not in result

    def test_gmail_reply_quoted_text_kept(self) -> None:
        proc = EmailProcessor(ProcessingConfig(quoted_text="keep"))
        result = proc._clean_content(GMAIL_REPLY_HTML, None)

        assert "I agree with the proposed timeline" in result
        assert "project timeline for Q1" in result


class TestSignatures:
    def test_signature_stripped_with_delimiter(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(HTML_WITH_SIGNATURE, None)

        assert "deployment is scheduled" in result
        assert "Jane Doe" not in result
        assert "+1-555-0199" not in result

    def test_signature_kept_when_disabled(self) -> None:
        proc = EmailProcessor(ProcessingConfig(strip_signatures=False))
        result = proc._clean_content(HTML_WITH_SIGNATURE, None)

        assert "deployment is scheduled" in result
        assert "Jane Doe" in result

    def test_regards_signature_detection(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(HTML_WITH_REGARDS_SIGNATURE, None)

        assert "contract and everything looks good" in result
        assert "proceed with signing" in result
        assert "John Smith" not in result
        assert "+1-555-0123" not in result

    def test_plain_text_fallback_strips_sent_from(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(None, PLAIN_TEXT_WITH_SIGNATURE)

        assert "API migration" in result
        assert "March release" in result
        assert "Sent from my iPhone" not in result


class TestTrackingAndInvisible:
    def test_tracking_pixel_removed(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(HTML_WITH_TRACKING, None)

        assert "Meeting notes" in result
        assert "sendgrid" not in result
        assert "1" not in result.split("standup")[1] if "standup" in result else True

    def test_hidden_elements_removed(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(HTML_WITH_TRACKING, None)

        assert "Meeting notes" in result
        assert "subscribed to updates" not in result


class TestProcessThread:
    def test_process_thread_returns_processed_thread(self) -> None:
        msg1 = _make_message(body_html=SIMPLE_HTML, message_id="msg-1")
        msg2 = _make_message(body_html=GMAIL_REPLY_HTML, message_id="msg-2")
        thread = _make_thread([msg1, msg2])

        proc = EmailProcessor()
        result = proc.process_thread(thread)

        assert isinstance(result, ProcessedThread)
        assert result.thread_id == "thread-1"
        assert result.subject == "Test Subject"
        assert len(result.messages) == 2
        assert result.messages[0].message_id == "msg-1"
        assert "**deadline**" in result.messages[0].content
        assert result.messages[1].message_id == "msg-2"
        assert "proposed timeline" in result.messages[1].content

    def test_empty_body_handled(self) -> None:
        proc = EmailProcessor()
        result = proc._clean_content(None, None)

        assert result == ""

    def test_whitespace_normalized(self) -> None:
        html = "<p>First paragraph</p><br/><br/><br/><br/><br/><p>Second paragraph</p>"
        proc = EmailProcessor()
        result = proc._clean_content(html, None)

        assert "First paragraph" in result
        assert "Second paragraph" in result
        # No more than 2 consecutive newlines
        assert "\n\n\n" not in result
