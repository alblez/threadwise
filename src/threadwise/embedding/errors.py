"""Embedding-specific exceptions."""


class EmbeddingError(Exception):
    """Raised when embedding a batch fails after exhausting retries."""

    def __init__(self, batch_index: int, original_error: Exception) -> None:
        self.batch_index = batch_index
        self.original_error = original_error
        super().__init__(
            f"Embedding failed for batch {batch_index}: {original_error}"
        )
