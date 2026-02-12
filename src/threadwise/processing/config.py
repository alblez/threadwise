"""Processing configuration for email content cleaning."""

from typing import Literal

from pydantic import BaseModel

DEFAULT_TRACKING_PATTERNS: list[str] = [
    "mailtrack",
    "sendgrid.net/wf/open",
    "list-manage.com/track",
    "mailchimp.com/track",
    "open.convertkit",
    "pixel.mailerlite",
    "tracking.hubspot",
]


class ProcessingConfig(BaseModel):
    """Configuration for the email processing pipeline."""

    strip_signatures: bool = True
    quoted_text: Literal["collapse", "strip", "keep"] = "collapse"
    tracking_patterns: list[str] = list(DEFAULT_TRACKING_PATTERNS)
