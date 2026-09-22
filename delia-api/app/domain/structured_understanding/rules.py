"""Deterministic Structured Understanding invariants (C3-T4 / C3-T4R1).

Reuses Evidence + model-invocation guards. Does not invent FACT from model output.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any

from app.domain.evidence.model import EpistemicClass, SourceRef
from app.domain.model_invocation.rules import (
    ModelInvocationDomainError,
    guard_invocation_payload,
)
from app.domain.structured_understanding.model import (
    LimitationNote,
    StructuredObservation,
    StructuredUnderstandingContent,
)


class StructuredUnderstandingDomainError(ValueError):
    """Domain invariant violation for structured understanding."""


ALLOWED_OBSERVATION_CLASSES = frozenset({EpistemicClass.OBSERVATION})

SCHEMA_SOURCE_OBSERVATION_V1 = "c3t4.source_observation_extraction"
SCHEMA_VERSION_V1 = "1"
REQUIRED_CONTENT_FIELDS = ("observations",)


def reject_world_fact_promotion(epistemic_class: EpistemicClass) -> None:
    if epistemic_class is EpistemicClass.FACT:
        raise StructuredUnderstandingDomainError(
            "source observation / model understanding must not become world FACT"
        )


def observation_is_not_world_fact(observation: StructuredObservation) -> bool:
    return observation.is_world_fact() is False


def parse_limitation_notes(raw: Any) -> tuple[LimitationNote, ...]:
    if raw is None:
        return ()
    if not isinstance(raw, Sequence) or isinstance(raw, (str, bytes)):
        raise StructuredUnderstandingDomainError("limitations must be a list")
    notes: list[LimitationNote] = []
    for item in raw:
        if isinstance(item, str):
            notes.append(LimitationNote(code=item))
            continue
        if not isinstance(item, Mapping):
            raise StructuredUnderstandingDomainError("limitation item must be string or object")
        code = item.get("code")
        if not isinstance(code, str) or not code.strip():
            raise StructuredUnderstandingDomainError("limitation.code is required")
        detail = item.get("detail")
        if detail is not None and not isinstance(detail, str):
            raise StructuredUnderstandingDomainError("limitation.detail must be string")
        notes.append(LimitationNote(code=code, detail=detail))
    return tuple(notes)


def parse_structured_observations(
    raw_observations: Any,
    *,
    bounded_source: SourceRef,
) -> tuple[StructuredObservation, ...]:
    if not isinstance(raw_observations, Sequence) or isinstance(raw_observations, (str, bytes)):
        raise StructuredUnderstandingDomainError("observations must be a list")
    observations: list[StructuredObservation] = []
    for item in raw_observations:
        if not isinstance(item, Mapping):
            raise StructuredUnderstandingDomainError("observation item must be an object")
        field_key = item.get("field_key")
        content = item.get("content")
        if not isinstance(field_key, str) or not field_key.strip():
            raise StructuredUnderstandingDomainError("observation.field_key is required")
        if not isinstance(content, str):
            raise StructuredUnderstandingDomainError("observation.content must be a string")
        declared = item.get("epistemic_class")
        if declared is None:
            epistemic = EpistemicClass.OBSERVATION
        elif isinstance(declared, str):
            try:
                epistemic = EpistemicClass(declared.strip().upper())
            except ValueError as exc:
                raise StructuredUnderstandingDomainError(
                    f"unsupported epistemic_class '{declared}'"
                ) from exc
        else:
            raise StructuredUnderstandingDomainError("observation.epistemic_class must be string")
        reject_world_fact_promotion(epistemic)
        if epistemic not in ALLOWED_OBSERVATION_CLASSES:
            raise StructuredUnderstandingDomainError(
                "C3-T4 observation items must be OBSERVATION"
            )
        limitations = parse_limitation_notes(item.get("limitations"))
        try:
            observations.append(
                StructuredObservation(
                    field_key=field_key,
                    content=content,
                    source_ref=bounded_source,
                    epistemic_class=epistemic,
                    limitations=limitations,
                )
            )
        except ValueError as exc:
            raise StructuredUnderstandingDomainError(str(exc)) from exc
    return tuple(observations)


def build_content_from_structured_output(
    structured_output: Mapping[str, Any],
    *,
    bounded_source: SourceRef,
) -> StructuredUnderstandingContent:
    try:
        guard_invocation_payload(dict(structured_output))
    except (ModelInvocationDomainError, ValueError) as exc:
        raise StructuredUnderstandingDomainError(str(exc)) from exc

    missing = [field for field in REQUIRED_CONTENT_FIELDS if field not in structured_output]
    if missing:
        raise StructuredUnderstandingDomainError(
            f"missing required fields: {', '.join(missing)}"
        )

    for forbidden in ("chain_of_thought", "cot", "tool_calls", "tool_call", "function_call"):
        if forbidden in structured_output:
            raise StructuredUnderstandingDomainError(
                f"forbidden field '{forbidden}' in structured understanding output"
            )

    claimed = structured_output.get("epistemic_class")
    if isinstance(claimed, str) and claimed.strip().upper() == EpistemicClass.FACT.value:
        raise StructuredUnderstandingDomainError(
            "model-claimed FACT is rejected for structured understanding result"
        )

    observations = parse_structured_observations(
        structured_output.get("observations"),
        bounded_source=bounded_source,
    )
    limitations = parse_limitation_notes(structured_output.get("limitations"))
    conflict_raw = structured_output.get("conflict_present", False)
    if not isinstance(conflict_raw, bool):
        raise StructuredUnderstandingDomainError("conflict_present must be boolean")

    if conflict_raw and not any(note.code == "conflicting_evidence" for note in limitations):
        limitations = limitations + (LimitationNote(code="conflicting_evidence"),)

    if not observations and not any(
        note.code in {"insufficient_evidence", "missing_support", "no_observation_produced"}
        for note in limitations
    ):
        limitations = limitations + (LimitationNote(code="no_observation_produced"),)

    return StructuredUnderstandingContent(
        observations=observations,
        limitations=limitations,
        conflict_present=conflict_raw,
    )
