"""Multimodal/media Evidence foundation domain (C3-MEDIA-FOUNDATION-01).

Provider-neutral semantics only — no capture/decode/provider runtime,
no biometric identity, no persistence, no execution path.
"""

from app.domain.media.model import (
    MediaKind,
    MediaObservation,
    MediaRef,
    MediaRegion,
    MediaTimeRange,
)

__all__ = [
    "MediaKind",
    "MediaObservation",
    "MediaRef",
    "MediaRegion",
    "MediaTimeRange",
]
