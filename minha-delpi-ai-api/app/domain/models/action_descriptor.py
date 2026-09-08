"""Contratos de catálogo OpenAPI para retrieval/planner."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class ActionDescriptor:
    action_id: str
    method: str = "GET"
    path: str = ""
    operation_id: str | None = None
    summary: str | None = None
    description: str | None = None
    provider_key: str | None = None
    provider_name: str | None = None
    sensitivity: str = "read"
    parameters_schema: tuple[dict[str, Any], ...] = ()
    request_body_schema: dict[str, Any] | None = None
    response_schema: dict[str, Any] | None = None
    tags: tuple[str, ...] = ()
    raw: dict[str, Any] = field(default_factory=dict, compare=False)

    @classmethod
    def from_action_dict(cls, action: dict[str, Any]) -> ActionDescriptor:
        parameters = action.get("parametersSchema") or action.get("parameters_schema") or []
        if not isinstance(parameters, list):
            parameters = []
        tags = action.get("tags") or []
        if not isinstance(tags, list):
            tags = []
        return cls(
            action_id=str(action.get("actionId") or action.get("action_id") or "").strip(),
            method=str(action.get("method") or "GET").upper(),
            path=str(action.get("path") or "").strip(),
            operation_id=(
                str(action.get("operationId") or action.get("operation_id") or "").strip()
                or None
            ),
            summary=str(action.get("summary") or "").strip() or None,
            description=str(action.get("description") or "").strip() or None,
            provider_key=str(action.get("providerKey") or action.get("provider_key") or "").strip()
            or None,
            provider_name=str(action.get("providerName") or action.get("provider_name") or "").strip()
            or None,
            sensitivity=str(action.get("sensitivity") or "read").strip() or "read",
            parameters_schema=tuple(item for item in parameters if isinstance(item, dict)),
            request_body_schema=(
                action.get("requestBodySchema")
                if isinstance(action.get("requestBodySchema"), dict)
                else (
                    action.get("request_body_schema")
                    if isinstance(action.get("request_body_schema"), dict)
                    else None
                )
            ),
            response_schema=(
                action.get("responseSchema")
                if isinstance(action.get("responseSchema"), dict)
                else (
                    action.get("response_schema")
                    if isinstance(action.get("response_schema"), dict)
                    else None
                )
            ),
            tags=tuple(str(item) for item in tags if str(item).strip()),
            raw=dict(action),
        )

    def as_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload.pop("raw", None)
        payload["actionId"] = payload.pop("action_id")
        payload["operationId"] = payload.pop("operation_id")
        payload["providerKey"] = payload.pop("provider_key")
        payload["providerName"] = payload.pop("provider_name")
        payload["parametersSchema"] = list(payload.pop("parameters_schema"))
        payload["requestBodySchema"] = payload.pop("request_body_schema")
        payload["responseSchema"] = payload.pop("response_schema")
        return payload


@dataclass(frozen=True)
class ActionCandidate:
    descriptor: ActionDescriptor
    score: float
    lexical_score: float = 0.0
    vector_score: float = 0.0
    reasons: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        base = self.descriptor.as_dict()
        base.update(
            {
                "selectionScore": round(float(self.score), 4),
                "selectionLexicalScore": round(float(self.lexical_score), 4),
                "selectionVectorScore": round(float(self.vector_score), 4),
                "selectionReasons": list(self.reasons),
            }
        )
        return base

    @property
    def action_id(self) -> str:
        return self.descriptor.action_id

    @property
    def raw_action(self) -> dict[str, Any]:
        return dict(self.descriptor.raw or self.descriptor.as_dict())
