"""Processing configuration for email content cleaning."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, model_validator

from threadwise.core.protocols import LLMProvider

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


class ChunkingConfig(BaseModel):
    """Configuration for thread chunking."""

    chunk_size: int = 512
    chunk_overlap: int = 50
    tokenizer: str = "cl100k_base"
    preserve_message_boundaries: bool = True


class SummarizationConfig(BaseModel):
    """Configuration for thread summarization."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    method: Literal["llm", "extractive"] = "llm"
    max_summary_tokens: int = 300
    llm_provider: LLMProvider | None = None
    llm_model: str | None = None
    context_window: int = 128000
    temperature: float = 0.0

    @model_validator(mode="after")
    def _validate_llm_provider(self) -> "SummarizationConfig":
        if self.method == "llm" and self.llm_provider is None:
            msg = "llm_provider is required when method is 'llm'"
            raise ValueError(msg)
        return self
