"""Email processing pipeline: HTML to clean markdown."""

import re

from bs4 import BeautifulSoup, Tag
from markdownify import markdownify

from threadwise.core.models import (
    EmailMessage,
    EmailThread,
    ProcessedMessage,
    ProcessedThread,
)
from threadwise.processing.config import ProcessingConfig

# Signature delimiter: line that is exactly "-- " or "--" (with optional trailing whitespace)
_SIGNATURE_DELIMITER_RE = re.compile(r"^--\s*$", re.MULTILINE)

# Closing salutation patterns
_SALUTATION_RE = re.compile(
    r"^(best regards|kind regards|regards|thanks|thank you|cheers|sincerely|warm regards"
    r"|with thanks|many thanks|all the best|cordially),?\s*$",
    re.IGNORECASE,
)

# Contact info patterns (phone numbers, URLs, email addresses)
_CONTACT_RE = re.compile(
    r"(\+?\d[\d\-\.\s\(\)]{7,})"  # phone number
    r"|(https?://\S+)"  # URL
    r"|(www\.\S+)"  # www URL
    r"|(\S+@\S+\.\S+)",  # email address
)

# Name-like line: 1-5 capitalized words, possibly with commas/periods
_NAME_LINE_RE = re.compile(r"^[A-Z][a-zA-Z\.\-]+(?: [A-Z][a-zA-Z\.\-]+){0,4}$")

# "Sent from my ..." pattern
_SENT_FROM_RE = re.compile(r"^sent from my\s", re.IGNORECASE)

# Quoted text: lines starting with ">" (markdown blockquotes)
_QUOTE_LINE_RE = re.compile(r"^>")


def _remove_tracking_pixels(soup: BeautifulSoup, patterns: list[str]) -> None:
    """Remove 1x1 tracking pixels and images from known tracking domains."""
    for img in soup.find_all("img"):
        if not isinstance(img, Tag):
            continue

        # Check for 1x1 or 0-dimension images
        width = img.get("width", "")
        height = img.get("height", "")
        if _is_tracking_dimension(str(width)) or _is_tracking_dimension(str(height)):
            img.decompose()
            continue

        # Check inline style for tiny dimensions
        style = str(img.get("style", ""))
        if re.search(r"(?:width|height)\s*:\s*[01]px", style):
            img.decompose()
            continue

        # Check src against tracking patterns
        src = str(img.get("src", ""))
        if any(pattern in src for pattern in patterns):
            img.decompose()


def _is_tracking_dimension(value: str) -> bool:
    """Check if a dimension value indicates a tracking pixel (0 or 1)."""
    stripped = value.strip().rstrip("px")
    return stripped in ("0", "1")


def _remove_invisible_elements(soup: BeautifulSoup) -> None:
    """Remove elements with display:none, visibility:hidden, or height:0."""
    for tag in soup.find_all(style=True):
        if not isinstance(tag, Tag):
            continue
        style = str(tag.get("style", "")).lower()
        if (
            "display:none" in style.replace(" ", "")
            or "visibility:hidden" in style.replace(" ", "")
            or re.search(r"height\s*:\s*0(?:px)?(?:\s*;|\s*$)", style)
        ):
            tag.decompose()


def _strip_signature_delimiter(text: str) -> str:
    """Remove signature blocks starting with '-- ' delimiter."""
    match = _SIGNATURE_DELIMITER_RE.search(text)
    if match:
        return text[: match.start()].rstrip()
    return text


def _strip_sent_from(text: str) -> str:
    """Remove 'Sent from my ...' lines."""
    lines = text.split("\n")
    result: list[str] = []
    for line in lines:
        if _SENT_FROM_RE.match(line.strip()):
            # Drop this line and any remaining lines (usually nothing follows)
            break
        result.append(line)
    return "\n".join(result)


def _strip_salutation_signature(text: str) -> str:
    """Remove signature blocks starting with a closing salutation.

    Only strips when the salutation is followed by name-like lines
    and/or contact info, to avoid false positives.
    """
    lines = text.split("\n")

    # Scan from the bottom to find potential salutation
    for i in range(len(lines) - 1, -1, -1):
        stripped = lines[i].strip()
        if not _SALUTATION_RE.match(stripped):
            continue

        # Check that remaining lines after salutation look like signature content
        remaining = [line.strip() for line in lines[i + 1 :] if line.strip()]
        if not remaining:
            # Salutation at end with nothing after — likely a real sign-off.
            # Be conservative: only strip if no substantial content before.
            continue

        if _looks_like_signature_block(remaining):
            return "\n".join(lines[:i]).rstrip()

    return text


def _looks_like_signature_block(lines: list[str]) -> bool:
    """Check if a sequence of lines looks like signature contact info."""
    if not lines:
        return False

    # First line should be name-like or a title/role
    has_name = _NAME_LINE_RE.match(lines[0]) is not None
    has_contact = any(_CONTACT_RE.search(line) for line in lines)

    # Need at least a name or contact info; with very few lines
    if len(lines) > 8:
        return False  # Too many lines, probably real content

    return has_name or has_contact


def _handle_quoted_text(text: str, mode: str) -> str:
    """Handle quoted reply blocks based on configuration mode."""
    if mode == "keep":
        return text

    lines = text.split("\n")
    result: list[str] = []
    in_quote_block = False

    for line in lines:
        is_quote = _QUOTE_LINE_RE.match(line) is not None

        if is_quote:
            if not in_quote_block:
                in_quote_block = True
                if mode == "collapse":
                    result.append("[Previous message quoted]")
                # "strip" mode: don't add anything
        else:
            in_quote_block = False
            result.append(line)

    return "\n".join(result)


def _normalize_whitespace(text: str) -> str:
    """Collapse multiple blank lines into maximum two and strip edges."""
    # Normalize whitespace-only lines to truly empty lines
    text = re.sub(r"^[ \t]+$", "", text, flags=re.MULTILINE)
    # Replace 3+ consecutive newlines with 2
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


class EmailProcessor:
    """Processes raw email threads into cleaned markdown content."""

    def __init__(self, config: ProcessingConfig | None = None) -> None:
        self._config = config or ProcessingConfig()

    def process_thread(self, thread: EmailThread) -> ProcessedThread:
        """Process all messages in a thread, returning cleaned content."""
        processed_messages = [self._process_message(msg) for msg in thread.messages]
        return ProcessedThread(
            thread_id=thread.thread_id,
            messages=processed_messages,
            subject=thread.subject,
        )

    def _process_message(self, message: EmailMessage) -> ProcessedMessage:
        """Process a single email message into cleaned markdown."""
        content = self._clean_content(message.body_html, message.body_text)
        return ProcessedMessage(
            message_id=message.message_id,
            thread_id=message.thread_id,
            sender=message.sender,
            recipients=message.recipients,
            date=message.date,
            subject=message.subject,
            content=content,
            in_reply_to=message.in_reply_to,
            attachments=message.attachments,
        )

    def _clean_content(self, body_html: str | None, body_text: str | None) -> str:
        """Run the full cleaning pipeline on email content."""
        # Step 1: Select body source
        if body_html:
            # Steps 2-4: HTML pipeline
            content = self._process_html(body_html)
        elif body_text:
            content = body_text
        else:
            return ""

        # Step 5: Strip signatures
        if self._config.strip_signatures:
            content = _strip_signature_delimiter(content)
            content = _strip_sent_from(content)
            content = _strip_salutation_signature(content)

        # Step 6: Handle quoted reply blocks
        content = _handle_quoted_text(content, self._config.quoted_text)

        # Step 7: Normalize whitespace
        content = _normalize_whitespace(content)

        return content

    def _process_html(self, html: str) -> str:
        """Clean HTML and convert to markdown."""
        soup = BeautifulSoup(html, "html.parser")

        # Step 2: Remove tracking pixels
        _remove_tracking_pixels(soup, self._config.tracking_patterns)

        # Step 3: Remove invisible elements
        _remove_invisible_elements(soup)

        # Step 4: Convert to markdown
        markdown: str = markdownify(str(soup), strip=["img"])
        return markdown
