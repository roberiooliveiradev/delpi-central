"""C3-T4 Structured Understanding domain package."""

from app.domain.structured_understanding.model import (
    LimitationNote,
    StructuredObservation,
    StructuredUnderstandingContent,
    StructuredUnderstandingId,
)
from app.domain.structured_understanding.rules import (
    StructuredUnderstandingDomainError,
    build_content_from_structured_output,
    observation_is_not_world_fact,
    reject_world_fact_promotion,
)

__all__ = [
    "LimitationNote",
    "StructuredObservation",
    "StructuredUnderstandingContent",
    "StructuredUnderstandingDomainError",
    "StructuredUnderstandingId",
    "build_content_from_structured_output",
    "observation_is_not_world_fact",
    "reject_world_fact_promotion",
]
