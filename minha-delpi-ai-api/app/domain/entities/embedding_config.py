from dataclasses import dataclass


@dataclass(frozen=True)
class EmbeddingConfig:
    provider: str
    base_url: str
    model: str
    api_key: str
    timeout_seconds: float
    dimensions: int
