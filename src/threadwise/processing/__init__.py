"""Email processing pipeline for threadwise."""

from threadwise.processing.config import ProcessingConfig
from threadwise.processing.email_processor import EmailProcessor

__all__ = ["EmailProcessor", "ProcessingConfig"]
