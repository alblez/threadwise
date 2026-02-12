"""Provider protocol interfaces for threadwise."""

from typing import Protocol, runtime_checkable


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Interface for embedding providers."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of texts. Returns list of vectors."""
        ...


@runtime_checkable
class LLMProvider(Protocol):
    """Interface for LLM providers."""

    def generate(self, prompt: str) -> str:
        """Generate text from a prompt. Returns the response string."""
        ...
