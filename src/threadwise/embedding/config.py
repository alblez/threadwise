"""Configuration for the embedding layer."""

from pydantic import BaseModel, ConfigDict

from threadwise.core.protocols import EmbeddingProvider


class EmbeddingConfig(BaseModel):
    """Configuration for the Embedder."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    provider: EmbeddingProvider
    model: str
    dimensions: int
    batch_size: int = 100
    max_retries: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
