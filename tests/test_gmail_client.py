"""Tests for GmailClient using mock Gmail API responses."""

from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from threadwise.gmail.client import GmailClient


@pytest.fixture()
def mock_service() -> MagicMock:
    return MagicMock()


@pytest.fixture()
def client(mock_service: MagicMock) -> GmailClient:
    with patch("threadwise.gmail.client.build", return_value=mock_service):
        return GmailClient(credentials=MagicMock())


def _set_thread_get(mock_service: MagicMock, fixture: dict[str, Any]) -> None:
    """Configure mock to return fixture data for threads().get()."""
    mock_service.users().threads().get().execute.return_value = fixture


def _set_thread_list(
    mock_service: MagicMock,
    thread_ids: list[str],
    fixtures: dict[str, dict[str, Any]],
) -> None:
    """Configure mock for threads().list() and threads().get() by ID."""
    mock_service.users().threads().list().execute.return_value = {
        "threads": [{"id": tid} for tid in thread_ids],
    }

    def get_side_effect(**kwargs: Any) -> MagicMock:
        result = MagicMock()
        result.execute.return_value = fixtures[kwargs["id"]]
        return result

    mock_service.users().threads().get.side_effect = get_side_effect


class TestGetThreadSimple:
    def test_get_thread_simple_parses_correctly(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_simple.json")
        _set_thread_get(mock_service, fixture)

        thread = client.get_thread("thread_simple_001")

        assert thread.thread_id == "thread_simple_001"
        assert thread.subject == "Project Proposal Follow-up"
        assert len(thread.messages) == 1

        msg = thread.messages[0]
        assert msg.sender == "alice@example.com"
        assert msg.recipients == ["bob@example.com"]
        assert msg.subject == "Project Proposal Follow-up"
        assert msg.body_text is not None
        assert "follow up on the project proposal" in msg.body_text
        assert msg.body_html is None
        assert msg.attachments == []
        assert msg.message_id == "<msg001@example.com>"


class TestGetThreadReplyChain:
    def test_get_thread_reply_chain_preserves_order(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_reply_chain.json")
        _set_thread_get(mock_service, fixture)

        thread = client.get_thread("thread_reply_001")

        assert thread.thread_id == "thread_reply_001"
        assert len(thread.messages) == 3
        assert thread.messages[0].date < thread.messages[1].date < thread.messages[2].date

    def test_get_thread_reply_chain_parses_html_body(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_reply_chain.json")
        _set_thread_get(mock_service, fixture)

        thread = client.get_thread("thread_reply_001")
        msg = thread.messages[0]

        assert msg.body_html is not None
        assert "<p>Hi Alice,</p>" in msg.body_html
        assert msg.body_text is not None
        assert "Thanks for following up" in msg.body_text


class TestGetThreadAttachments:
    def test_get_thread_attachments_extracts_metadata(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_attachments.json")
        _set_thread_get(mock_service, fixture)

        thread = client.get_thread("thread_attach_001")
        msg = thread.messages[0]

        assert len(msg.attachments) == 2
        assert msg.attachments[0].filename == "Q4_Report.pdf"
        assert msg.attachments[0].mime_type == "application/pdf"
        assert msg.attachments[0].size == 245760
        assert msg.attachments[1].filename == "architecture_diagram.png"
        assert msg.attachments[1].mime_type == "image/png"
        assert msg.attachments[1].size == 102400

    def test_get_thread_attachments_does_not_download_content(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_attachments.json")
        _set_thread_get(mock_service, fixture)

        client.get_thread("thread_attach_001")

        mock_service.users().messages().attachments().get.assert_not_called()


class TestListThreads:
    def test_list_threads_with_query(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_simple.json")
        _set_thread_list(
            mock_service,
            ["thread_simple_001"],
            {"thread_simple_001": fixture},
        )

        threads = client.list_threads(query="subject:proposal")

        assert len(threads) == 1
        call_kwargs = mock_service.users().threads().list.call_args
        assert call_kwargs is not None
        assert call_kwargs[1]["q"] == "subject:proposal"

    def test_list_threads_with_labels(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_simple.json")
        _set_thread_list(
            mock_service,
            ["thread_simple_001"],
            {"thread_simple_001": fixture},
        )

        threads = client.list_threads(labels=["INBOX"])

        assert len(threads) == 1
        call_kwargs = mock_service.users().threads().list.call_args
        assert call_kwargs is not None
        assert call_kwargs[1]["labelIds"] == ["INBOX"]

    def test_list_threads_respects_max_results(
        self,
        client: GmailClient,
        mock_service: MagicMock,
        load_fixture: Any,
    ) -> None:
        fixture = load_fixture("gmail_thread_simple.json")
        _set_thread_list(
            mock_service,
            ["thread_simple_001", "thread_simple_001"],
            {"thread_simple_001": fixture},
        )

        threads = client.list_threads(max_results=1)

        assert len(threads) == 1


class TestEdgeCases:
    def test_get_thread_missing_subject(
        self,
        client: GmailClient,
        mock_service: MagicMock,
    ) -> None:
        raw_thread: dict[str, Any] = {
            "id": "thread_no_subj",
            "messages": [
                {
                    "id": "msg_no_subj",
                    "threadId": "thread_no_subj",
                    "internalDate": "1700000000000",
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [
                            {"name": "From", "value": "alice@example.com"},
                            {"name": "To", "value": "bob@example.com"},
                        ],
                        "body": {"size": 0},
                        "parts": [],
                    },
                }
            ],
        }
        _set_thread_get(mock_service, raw_thread)

        thread = client.get_thread("thread_no_subj")

        assert thread.subject is None
        assert thread.messages[0].subject is None

    def test_get_thread_plain_text_fallback(
        self,
        client: GmailClient,
        mock_service: MagicMock,
    ) -> None:
        raw_thread: dict[str, Any] = {
            "id": "thread_plain",
            "messages": [
                {
                    "id": "msg_plain",
                    "threadId": "thread_plain",
                    "internalDate": "1700000000000",
                    "payload": {
                        "mimeType": "text/plain",
                        "headers": [
                            {"name": "From", "value": "alice@example.com"},
                            {"name": "To", "value": "bob@example.com"},
                            {"name": "Subject", "value": "Plain text only"},
                            {"name": "Date", "value": "Tue, 14 Nov 2023 14:13:20 +0000"},
                        ],
                        "body": {
                            "size": 11,
                            "data": "SGVsbG8gV29ybGQ=",
                        },
                        "parts": [],
                    },
                }
            ],
        }
        _set_thread_get(mock_service, raw_thread)

        thread = client.get_thread("thread_plain")
        msg = thread.messages[0]

        assert msg.body_text == "Hello World"
        assert msg.body_html is None
