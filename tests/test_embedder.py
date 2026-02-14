"""Tests for the embedding layer."""

import hashlib
from unittest.mock import patch

import pytest

from threadwise.core.models import Chunk, ChunkMetadata
from threadwise.embedding.config import EmbeddingConfig
from threadwise.embedding.embedder import Embedder
from threadwise.embedding.errors import EmbeddingError

DIMENSIONS = 384


class MockEmbeddingProvider:
    """Deterministic embedding provider for testing."""

    def __init__(self, dimensions: int = DIMENSIONS) -> None:
        self.dimensions = dimensions
        self.call_count = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.call_count += 1
        return [self._hash_vector(t) for t in texts]

    def _hash_vector(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode()).hexdigest()
        values = [int(digest[i : i + 2], 16) / 255.0 for i in range(0, len(digest), 2)]
        # Repeat to fill dimensions
        full = (values * ((self.dimensions // len(values)) + 1))[: self.dimensions]
        return full


class RateLimitProvider:
    """Provider that fails N times with a rate-limit error, then succeeds."""

    def __init__(self, fail_count: int, dimensions: int = DIMENSIONS) -> None:
        self.fail_count = fail_count
        self.dimensions = dimensions
        self.attempt = 0

    def embed(self, texts: list[str]) -> list[list[float]]:
        self.attempt += 1
        if self.attempt <= self.fail_count:
            raise RuntimeError("rate limit exceeded (429)")
        return [[0.1] * self.dimensions for _ in texts]


class AlwaysFailProvider:
    """Provider that always raises a rate-limit error."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise RuntimeError("429 rate limit exceeded")


class NonRateLimitFailProvider:
    """Provider that raises a non-rate-limit error."""

    def embed(self, texts: list[str]) -> list[list[float]]:
        raise ValueError("invalid input format")


def _make_chunk(text: str, index: int = 0) -> Chunk:
    return Chunk(
        id=f"chunk-{index}",
        text=text,
        metadata=ChunkMetadata(
            project_id="proj-1",
            source_type="email",
            source_id="thread-1",
            chunk_index=index,
        ),
    )


def _make_config(provider: object, **overrides: object) -> EmbeddingConfig:
    defaults = {
        "provider": provider,
        "model": "test-model",
        "dimensions": DIMENSIONS,
        "base_delay": 0.001,
        "max_delay": 0.01,
    }
    defaults.update(overrides)
    return EmbeddingConfig(**defaults)  # type: ignore[arg-type]


class TestEmbedChunks:
    def test_embed_chunks_assigns_vectors(self) -> None:
        provider = MockEmbeddingProvider()
        config = _make_config(provider)
        embedder = Embedder(config)
        chunks = [_make_chunk(f"text {i}", i) for i in range(3)]

        result = embedder.embed_chunks(chunks)

        assert len(result) == 3
        for chunk in result:
            assert chunk.embedding is not None
            assert len(chunk.embedding) == DIMENSIONS

    def test_single_chunk_works(self) -> None:
        provider = MockEmbeddingProvider()
        config = _make_config(provider, batch_size=100)
        embedder = Embedder(config)
        chunks = [_make_chunk("single")]

        result = embedder.embed_chunks(chunks)

        assert len(result) == 1
        assert result[0].embedding is not None
        assert len(result[0].embedding) == DIMENSIONS

    def test_empty_list_returns_empty(self) -> None:
        provider = MockEmbeddingProvider()
        config = _make_config(provider)
        embedder = Embedder(config)

        result = embedder.embed_chunks([])

        assert result == []

    def test_chunks_retain_metadata_after_embedding(self) -> None:
        provider = MockEmbeddingProvider()
        config = _make_config(provider)
        embedder = Embedder(config)
        chunk = Chunk(
            id="meta-chunk",
            text="hello world",
            metadata=ChunkMetadata(
                project_id="proj-1",
                source_type="email",
                source_id="thread-1",
                chunk_index=0,
                author="alice@example.com",
                subject="Budget Q3",
                thread_context="Discussion about Q3 budget.",
            ),
        )

        result = embedder.embed_chunks([chunk])

        assert result[0].metadata.author == "alice@example.com"
        assert result[0].metadata.subject == "Budget Q3"
        assert result[0].metadata.thread_context == "Discussion about Q3 budget."

    def test_embed_chunks_preserves_order(self) -> None:
        provider = MockEmbeddingProvider()
        config = _make_config(provider, batch_size=2)
        embedder = Embedder(config)
        texts = [f"unique text number {i}" for i in range(5)]
        chunks = [_make_chunk(t, i) for i, t in enumerate(texts)]

        result = embedder.embed_chunks(chunks)

        # Recompute expected vectors directly
        expected = provider.embed(texts)
        for i, chunk in enumerate(result):
            assert chunk.embedding == expected[i], f"Mismatch at index {i}"


class TestEmbedTexts:
    def test_embed_texts_returns_correct_shape(self) -> None:
        provider = MockEmbeddingProvider()
        config = _make_config(provider)
        embedder = Embedder(config)
        texts = [f"text {i}" for i in range(5)]

        result = embedder.embed_texts(texts)

        assert len(result) == 5
        for vec in result:
            assert len(vec) == DIMENSIONS

    def test_batching_splits_correctly(self) -> None:
        provider = MockEmbeddingProvider()
        config = _make_config(provider, batch_size=3)
        embedder = Embedder(config)
        texts = [f"text {i}" for i in range(10)]

        embedder.embed_texts(texts)

        assert provider.call_count == 4  # 3+3+3+1


class TestRetryBehavior:
    def test_rate_limit_retry_succeeds(self) -> None:
        provider = RateLimitProvider(fail_count=2)
        config = _make_config(provider, max_retries=3)
        embedder = Embedder(config)
        chunks = [_make_chunk("text", 0)]

        result = embedder.embed_chunks(chunks)

        assert result[0].embedding is not None
        assert len(result[0].embedding) == DIMENSIONS

    def test_rate_limit_exhausted_raises_embedding_error(self) -> None:
        provider = AlwaysFailProvider()
        config = _make_config(provider, max_retries=2)
        embedder = Embedder(config)
        chunks = [_make_chunk("text", 0)]

        with pytest.raises(EmbeddingError) as exc_info:
            embedder.embed_chunks(chunks)

        assert exc_info.value.batch_index == 0
        assert isinstance(exc_info.value.original_error, RuntimeError)

    def test_non_rate_limit_errors_propagate_immediately(self) -> None:
        provider = NonRateLimitFailProvider()
        config = _make_config(provider, max_retries=3)
        embedder = Embedder(config)
        chunks = [_make_chunk("text", 0)]

        with pytest.raises(ValueError, match="invalid input format"):
            embedder.embed_chunks(chunks)

    def test_backoff_delay_respects_max_delay(self) -> None:
        provider = AlwaysFailProvider()
        config = _make_config(provider, max_retries=5, base_delay=10.0, max_delay=15.0)
        embedder = Embedder(config)

        sleep_calls: list[float] = []

        def record_sleep(d: float) -> None:
            sleep_calls.append(d)

        with (
            patch("threadwise.embedding.embedder.time.sleep", side_effect=record_sleep),
            pytest.raises(EmbeddingError),
        ):
            embedder.embed_texts(["text"])

        assert len(sleep_calls) == 4  # 5 retries - 1 (last attempt raises)
        for delay in sleep_calls:
            assert delay <= 15.0 + 1.0  # max_delay + max jitter
