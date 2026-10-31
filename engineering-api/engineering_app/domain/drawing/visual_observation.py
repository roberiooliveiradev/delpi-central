"""DrawingVisualObservation — untrusted consumer input (doc 71 G1/§4.1).

Visual observations are produced by the ChatGPT model's perception of a
drawing shown in the conversation. They are NEVER official facts and
must be parsed through `parse_visual_observations` — strict schema,
hard limits, unknown keys rejected, text treated as untrusted data.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
from typing import Any

MAX_OBSERVATIONS = 50
MAX_TEXT_LEN = 500
MAX_ID_LEN = 80

ALLOWED_KINDS = {
    "text", "dimension", "material", "note", "bom_item", "symbol",
    "legibility", "revision", "identification", "other",
}
ALLOWED_CONFIDENCE = {"low", "medium", "high"}
CAPTURE_METHOD = "chatgpt_visual"


class ObservationKind(StrEnum):
    TEXT = "text"
    DIMENSION = "dimension"
    MATERIAL = "material"
    NOTE = "note"
    BOM_ITEM = "bom_item"
    SYMBOL = "symbol"
    LEGIBILITY = "legibility"
    REVISION = "revision"
    IDENTIFICATION = "identification"
    OTHER = "other"


@dataclass
class DocumentIdentity:
    source: str = "user_attachment"  # user_attachment | official_drawing
    document_ref: str | None = None
    document_hash: str | None = None
    revision: str | None = None
    product_code: str | None = None


@dataclass
class DrawingVisualObservation:
    observation_id: str
    kind: str
    raw_observation: str
    document_identity: DocumentIdentity = field(
        default_factory=DocumentIdentity
    )
    page: int | None = None
    view_or_region: str | None = None
    normalized_value: str | None = None
    unit: str | None = None
    confidence: str = "medium"
    uncertainty_reason: str | None = None
    capture_method: str = CAPTURE_METHOD
    is_hypothesis: bool = False

    def to_dict(self) -> dict[str, Any]:
        out = asdict(self)
        out["capture_method"] = CAPTURE_METHOD
        return out


class VisualObservationError(ValueError):
    """Observation payload violates the contract."""


def _clip(value: Any, limit: int = MAX_TEXT_LEN) -> str | None:
    if value is None:
        return None
    text = str(value).strip()
    return text[:limit] or None


def parse_visual_observations(payload: Any) -> list[DrawingVisualObservation]:
    """Validate+normalize untrusted consumer observations."""
    if payload is None:
        return []
    if not isinstance(payload, list):
        raise VisualObservationError(
            "invalid_visual_observation:payload_must_be_list"
        )
    if len(payload) > MAX_OBSERVATIONS:
        raise VisualObservationError(
            f"invalid_visual_observation:max_{MAX_OBSERVATIONS}_items"
        )
    out: list[DrawingVisualObservation] = []
    seen_ids: set[str] = set()
    for index, raw in enumerate(payload):
        if not isinstance(raw, dict):
            raise VisualObservationError(
                f"invalid_visual_observation:item_{index}_not_object"
            )
        allowed = {
            "observation_id", "document_identity", "page",
            "view_or_region", "kind", "raw_observation",
            "normalized_value", "unit", "confidence",
            "uncertainty_reason", "is_hypothesis",
        }
        unknown = set(raw) - allowed
        if unknown:
            raise VisualObservationError(
                f"invalid_visual_observation:item_{index}_unknown_fields:"
                f"{sorted(unknown)}"
            )
        kind = str(raw.get("kind") or "other").strip().lower()
        if kind not in ALLOWED_KINDS:
            raise VisualObservationError(
                f"invalid_visual_observation:item_{index}_kind:{kind}"
            )
        text = _clip(raw.get("raw_observation"))
        if not text:
            raise VisualObservationError(
                f"invalid_visual_observation:item_{index}_empty"
            )
        ident_raw = raw.get("document_identity") or {}
        if not isinstance(ident_raw, dict):
            raise VisualObservationError(
                f"invalid_visual_observation:item_{index}_identity"
            )
        identity = DocumentIdentity(
            source=str(ident_raw.get("source") or "user_attachment"),
            document_ref=_clip(ident_raw.get("document_ref"), MAX_ID_LEN),
            document_hash=_clip(ident_raw.get("document_hash"), MAX_ID_LEN),
            revision=_clip(ident_raw.get("revision"), 20),
            product_code=_clip(ident_raw.get("product_code"), 20),
        )
        page = raw.get("page")
        if page is not None and (
            not isinstance(page, int) or page < 1 or page > 999
        ):
            raise VisualObservationError(
                f"invalid_visual_observation:item_{index}_page"
            )
        confidence = str(raw.get("confidence") or "medium").lower()
        if confidence not in ALLOWED_CONFIDENCE:
            confidence = "low"
        obs_id = _clip(raw.get("observation_id"), MAX_ID_LEN) or (
            f"VO-{index + 1:03d}"
        )
        if obs_id in seen_ids:
            obs_id = f"{obs_id}#{index + 1}"
        seen_ids.add(obs_id)
        out.append(
            DrawingVisualObservation(
                observation_id=obs_id,
                kind=kind,
                raw_observation=text,
                document_identity=identity,
                page=page,
                view_or_region=_clip(raw.get("view_or_region"), 120),
                normalized_value=_clip(raw.get("normalized_value")),
                unit=_clip(raw.get("unit"), 12),
                confidence=confidence,
                uncertainty_reason=_clip(raw.get("uncertainty_reason")),
                is_hypothesis=bool(raw.get("is_hypothesis")),
            )
        )
    return out
