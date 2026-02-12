"""Gmail API client for fetching threads and messages."""

import base64
import email.utils
from datetime import UTC, datetime
from typing import Any

from google.auth.credentials import Credentials
from googleapiclient.discovery import build  # type: ignore[import-untyped]

from threadwise.core.models import AttachmentMetadata, EmailMessage, EmailThread


def _get_header(headers: list[dict[str, str]], name: str) -> str | None:
    """Case-insensitive header lookup."""
    name_lower = name.lower()
    for header in headers:
        if header["name"].lower() == name_lower:
            return header["value"]
    return None


def _parse_email_address(raw: str) -> str:
    """Extract email address from a header value like 'Name <addr>'."""
    _, addr = email.utils.parseaddr(raw)
    return addr if addr else raw


def _parse_recipients(to_header: str | None, cc_header: str | None) -> list[str]:
    """Parse To and Cc headers into a flat list of email addresses."""
    combined = ", ".join(h for h in [to_header, cc_header] if h)
    if not combined:
        return []
    return [addr for _, addr in email.utils.getaddresses([combined]) if addr]


def _parse_date(date_str: str | None, internal_date: str | None) -> datetime:
    """Parse RFC 2822 date string, falling back to Gmail internalDate (epoch ms)."""
    if date_str:
        try:
            return email.utils.parsedate_to_datetime(date_str)
        except (ValueError, TypeError):
            pass
    if internal_date:
        return datetime.fromtimestamp(int(internal_date) / 1000, tz=UTC)
    return datetime.now(tz=UTC)


def _decode_body(data: str) -> str:
    """Decode base64url-encoded body data to UTF-8 string."""
    return base64.urlsafe_b64decode(data).decode("utf-8")


def _extract_bodies(payload: dict[str, Any]) -> tuple[str | None, str | None]:
    """Recursively walk MIME parts to extract text/plain and text/html bodies."""
    mime_type: str = payload.get("mimeType", "")
    body_data: str | None = payload.get("body", {}).get("data")

    if mime_type == "text/plain" and body_data:
        return _decode_body(body_data), None
    if mime_type == "text/html" and body_data:
        return None, _decode_body(body_data)

    parts: list[dict[str, Any]] = payload.get("parts", [])
    body_text: str | None = None
    body_html: str | None = None

    for part in parts:
        t, h = _extract_bodies(part)
        if t and not body_text:
            body_text = t
        if h and not body_html:
            body_html = h

    return body_text, body_html


def _extract_attachments(payload: dict[str, Any]) -> list[AttachmentMetadata]:
    """Recursively walk MIME parts to collect attachment metadata."""
    attachments: list[AttachmentMetadata] = []

    filename: str = payload.get("filename", "")
    attachment_id: str | None = payload.get("body", {}).get("attachmentId")

    if filename and attachment_id:
        attachments.append(
            AttachmentMetadata(
                filename=filename,
                mime_type=payload.get("mimeType", "application/octet-stream"),
                size=payload.get("body", {}).get("size", 0),
            )
        )

    for part in payload.get("parts", []):
        attachments.extend(_extract_attachments(part))

    return attachments


def _parse_message(raw_message: dict[str, Any]) -> EmailMessage:
    """Parse a raw Gmail API message dict into an EmailMessage."""
    payload: dict[str, Any] = raw_message["payload"]
    headers: list[dict[str, str]] = payload.get("headers", [])

    message_id_header = _get_header(headers, "Message-ID")
    message_id = message_id_header if message_id_header else raw_message["id"]

    sender_raw = _get_header(headers, "From") or ""
    sender = _parse_email_address(sender_raw)

    to_header = _get_header(headers, "To")
    cc_header = _get_header(headers, "Cc")
    recipients = _parse_recipients(to_header, cc_header)

    date = _parse_date(
        _get_header(headers, "Date"),
        raw_message.get("internalDate"),
    )

    subject = _get_header(headers, "Subject")
    in_reply_to = _get_header(headers, "In-Reply-To")

    body_text, body_html = _extract_bodies(payload)
    attachments = _extract_attachments(payload)

    return EmailMessage(
        message_id=message_id,
        thread_id=raw_message["threadId"],
        sender=sender,
        recipients=recipients,
        date=date,
        subject=subject,
        body_html=body_html,
        body_text=body_text,
        in_reply_to=in_reply_to,
        attachments=attachments,
    )


def _parse_thread(raw_thread: dict[str, Any]) -> EmailThread:
    """Parse a raw Gmail API thread dict into an EmailThread."""
    messages = [_parse_message(msg) for msg in raw_thread.get("messages", [])]
    subject = messages[0].subject if messages else None
    return EmailThread(
        thread_id=raw_thread["id"],
        messages=messages,
        subject=subject,
    )


class GmailClient:
    """Gmail API client for fetching threads and messages."""

    def __init__(self, credentials: Credentials) -> None:
        self._service: Any = build("gmail", "v1", credentials=credentials)

    def get_thread(self, thread_id: str) -> EmailThread:
        """Fetch a single thread by ID and return a structured EmailThread."""
        raw: dict[str, Any] = (
            self._service.users()
            .threads()
            .get(userId="me", id=thread_id, format="full")
            .execute()
        )
        return _parse_thread(raw)

    def list_threads(
        self,
        query: str | None = None,
        labels: list[str] | None = None,
        max_results: int = 50,
    ) -> list[EmailThread]:
        """List threads matching query/labels and return structured EmailThreads."""
        threads: list[EmailThread] = []
        page_token: str | None = None

        while len(threads) < max_results:
            request_kwargs: dict[str, Any] = {
                "userId": "me",
                "maxResults": min(max_results - len(threads), 100),
            }
            if query:
                request_kwargs["q"] = query
            if labels:
                request_kwargs["labelIds"] = labels
            if page_token:
                request_kwargs["pageToken"] = page_token

            response: dict[str, Any] = (
                self._service.users().threads().list(**request_kwargs).execute()
            )

            thread_summaries: list[dict[str, Any]] = response.get("threads", [])
            if not thread_summaries:
                break

            for summary in thread_summaries:
                if len(threads) >= max_results:
                    break
                threads.append(self.get_thread(summary["id"]))

            page_token = response.get("nextPageToken")
            if not page_token:
                break

        return threads
