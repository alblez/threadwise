"""Embedder: batching and retry logic for embedding providers.

Rate-limit detection heuristic: when a provider raises an exception, the
Embedder inspects the string representation of the error for common
rate-limit signals ("rate limit", "429", "too many requests",
case-insensitive). Matching errors are retried with exponential backoff
and jitter. Non-matching errors propagate immediately. Provider
implementors should ensure their rate-limit exceptions contain one of
these phrases so the retry logic activates correctly.
"""

import random
import time

from threadwise.core.models import Chunk
from threadwise.embedding.config import EmbeddingConfig
from threadwise.embedding.errors import EmbeddingError

_RATE_LIMIT_SIGNALS = ("rate limit", "429", "too many requests")


def _is_rate_limit_error(exc: Exception) -> bool:
    msg = str(exc).lower()
    return any(signal in msg for signal in _RATE_LIMIT_SIGNALS)


class Embedder:
    """Embeds text chunks using a configured EmbeddingProvider.

    Handles batching, exponential-backoff retries for rate-limit errors,
    and vector assignment to Chunk objects.
    """

    def __init__(self, config: EmbeddingConfig) -> None:
        self._config = config

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Embed a list of texts with batching and retry logic.

        Returns a list of embedding vectors in the same order as the input.
        """
        if not texts:
            return []

        all_embeddings: list[list[float]] = []
        batch_size = self._config.batch_size

        for batch_idx, start in enumerate(range(0, len(texts), batch_size)):
            batch = texts[start : start + batch_size]
            embeddings = self._embed_batch_with_retry(batch, batch_idx)
            all_embeddings.extend(embeddings)

        return all_embeddings

    def embed_chunks(self, chunks: list[Chunk]) -> list[Chunk]:
        """Embed chunks in place, assigning vectors to each chunk's embedding field."""
        if not chunks:
            return chunks

        texts = [chunk.text for chunk in chunks]
        embeddings = self.embed_texts(texts)

        for chunk, vector in zip(chunks, embeddings, strict=True):
            chunk.embedding = vector

        return chunks

    def _embed_batch_with_retry(
        self, batch: list[str], batch_index: int
    ) -> list[list[float]]:
        max_retries = self._config.max_retries
        base_delay = self._config.base_delay
        max_delay = self._config.max_delay

        for attempt in range(max_retries):
            try:
                return self._config.provider.embed(batch)
            except Exception as exc:
                if not _is_rate_limit_error(exc):
                    raise
                if attempt == max_retries - 1:
                    raise EmbeddingError(batch_index, exc) from exc
                delay = min(base_delay * (2**attempt) + random.uniform(0, 1), max_delay)
                time.sleep(delay)

        raise EmbeddingError(batch_index, RuntimeError("max retries exhausted"))  # pragma: no cover
