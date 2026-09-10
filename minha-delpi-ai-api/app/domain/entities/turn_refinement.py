"""Turn Refinement — contrato canônico de refinamento multi-turn (E3.S3).

Proposta estruturada de delta de argumentos/apresentação sobre uma referência
alvo (action/result/topic). Path/operationId não são chaves de decisão
semântica neste contrato.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

TURN_REFINEMENT_CONTRACT_VERSION = 1

SUPPORTED_TARGET_KINDS = frozenset({"action", "result_set", "topic", "unknown"})
SUPPORTED_REFINEMENT_KINDS = frozenset(
    {
        "argument_delta",
        "presentation_delta",
        "clarify",
        "no_op",
        "unknown",
    }
)

# Chaves proibidas na superfície semântica (decisão). Podem existir em legado,
# mas são stripadas do contrato canônico.
FORBIDDEN_SEMANTIC_KEYS = frozenset(
    {
        "path",
        "previous_path",
        "previousPath",
        "pathToken",
        "path_token",
        "pathContains",
        "path_contains",
        "pathMarkers",
        "path_markers",
        "routeSegment",
        "route_segment",
        "operationId",
        "operation_id",
        "parameterStrategy",
        "parameter_strategy",
        "preferredRouteId",
        "preferred_route_id",
        "operational_route_id",
        "operationalRouteId",
    }
)

TURN_REFINEMENT_JSON_SCHEMA: dict[str, Any] = {
    "$schema": "https://json-schema.org/draft/2020-12/schema",
    "title": "TurnRefinement",
    "type": "object",
    "required": ["kind", "confidence"],
    "additionalProperties": True,
    "properties": {
        "contractVersion": {"type": "integer", "minimum": 1},
        "kind": {"type": "string"},
        "target": {
            "type": ["object", "null"],
            "properties": {
                "kind": {"type": "string"},
                "actionId": {"type": ["string", "null"]},
                "resultSetId": {"type": ["string", "null"]},
                "topicId": {"type": ["string", "null"]},
                "ordinal": {"type": ["integer", "null"]},
            },
        },
        "argumentDelta": {"type": "object"},
        "clearedArguments": {"type": "array", "items": {"type": "string"}},
        "presentationDelta": {"type": ["object", "null"]},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "clarification": {"type": ["object", "null"]},
        "conflicts": {"type": "array"},
        "reason": {"type": "string"},
        "source": {"type": "string"},
    },
}


def _strip_forbidden(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict):
        return {}
    cleaned: dict[str, Any] = {}
    for key, value in raw.items():
        name = str(key or "").strip()
        if not name or name in FORBIDDEN_SEMANTIC_KEYS:
            continue
        cleaned[name] = value
    return cleaned


def _clean_argument_delta(raw: Any) -> dict[str, Any]:
    cleaned = _strip_forbidden(raw)
    # Normalize common aliases to OpenAPI-ish names without inventing values.
    aliases = {
        "pageSize": "page_size",
        "page_size": "page_size",
        "groupBy": "group_by",
        "group_by": "group_by",
        "productCode": "product_code",
        "product_code": "product_code",
        "branch": "branch",
        "warehouse": "warehouse",
        "page": "page",
        "maxDepth": "max_depth",
        "max_depth": "max_depth",
    }
    normalized: dict[str, Any] = {}
    for key, value in cleaned.items():
        target = aliases.get(key, key)
        if value is None:
            continue
        if isinstance(value, str) and not value.strip():
            continue
        normalized[target] = value
    return normalized


@dataclass(frozen=True)
class TurnRefinementTarget:
    kind: str = "unknown"
    action_id: str | None = None
    result_set_id: str | None = None
    topic_id: str | None = None
    ordinal: int | None = None

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": self.kind}
        if self.action_id:
            payload["actionId"] = self.action_id
        if self.result_set_id:
            payload["resultSetId"] = self.result_set_id
        if self.topic_id:
            payload["topicId"] = self.topic_id
        if self.ordinal is not None:
            payload["ordinal"] = self.ordinal
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> TurnRefinementTarget | None:
        if not isinstance(payload, dict):
            return None
        kind = str(payload.get("kind") or "unknown").strip().lower() or "unknown"
        if kind not in SUPPORTED_TARGET_KINDS:
            kind = "unknown"
        ordinal_raw = payload.get("ordinal")
        ordinal: int | None
        try:
            ordinal = int(ordinal_raw) if ordinal_raw is not None else None
        except (TypeError, ValueError):
            ordinal = None
        return cls(
            kind=kind,
            action_id=(
                str(payload.get("actionId") or payload.get("action_id") or "").strip()
                or None
            ),
            result_set_id=(
                str(
                    payload.get("resultSetId") or payload.get("result_set_id") or ""
                ).strip()
                or None
            ),
            topic_id=(
                str(payload.get("topicId") or payload.get("topic_id") or "").strip()
                or None
            ),
            ordinal=ordinal,
        )


@dataclass(frozen=True)
class TurnRefinementClarification:
    reason: str
    prompt_hint: str | None = None
    candidates: tuple[str, ...] = ()

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {"reason": self.reason}
        if self.prompt_hint:
            payload["promptHint"] = self.prompt_hint
        if self.candidates:
            payload["candidates"] = list(self.candidates)
        return payload

    @classmethod
    def from_dict(
        cls, payload: dict[str, Any] | None
    ) -> TurnRefinementClarification | None:
        if not isinstance(payload, dict):
            return None
        reason = str(payload.get("reason") or "").strip()
        if not reason:
            return None
        candidates_raw = payload.get("candidates") or ()
        candidates = tuple(
            str(item).strip() for item in candidates_raw if str(item or "").strip()
        )
        return cls(
            reason=reason,
            prompt_hint=(
                str(
                    payload.get("promptHint") or payload.get("prompt_hint") or ""
                ).strip()
                or None
            ),
            candidates=candidates,
        )


@dataclass(frozen=True)
class TurnRefinementConflict:
    argument: str
    inherited_value: Any
    proposed_value: Any
    resolution: str = "explicit_wins"

    def as_dict(self) -> dict[str, Any]:
        return {
            "argument": self.argument,
            "inheritedValue": self.inherited_value,
            "proposedValue": self.proposed_value,
            "resolution": self.resolution,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> TurnRefinementConflict | None:
        if not isinstance(payload, dict):
            return None
        argument = str(payload.get("argument") or "").strip()
        if not argument or argument in FORBIDDEN_SEMANTIC_KEYS:
            return None
        return cls(
            argument=argument,
            inherited_value=payload.get("inheritedValue", payload.get("inherited_value")),
            proposed_value=payload.get("proposedValue", payload.get("proposed_value")),
            resolution=str(payload.get("resolution") or "explicit_wins").strip()
            or "explicit_wins",
        )


@dataclass(frozen=True)
class TurnRefinement:
    kind: str
    confidence: float
    target: TurnRefinementTarget | None = None
    argument_delta: dict[str, Any] = field(default_factory=dict)
    cleared_arguments: tuple[str, ...] = ()
    presentation_delta: dict[str, Any] | None = None
    clarification: TurnRefinementClarification | None = None
    conflicts: tuple[TurnRefinementConflict, ...] = ()
    reason: str = ""
    source: str = "heuristic"
    contract_version: int = TURN_REFINEMENT_CONTRACT_VERSION

    def as_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "contractVersion": self.contract_version,
            "kind": self.kind,
            "confidence": self.confidence,
            "argumentDelta": dict(self.argument_delta),
            "clearedArguments": list(self.cleared_arguments),
            "conflicts": [item.as_dict() for item in self.conflicts],
            "reason": self.reason,
            "source": self.source,
        }
        if self.target is not None:
            payload["target"] = self.target.as_dict()
        if self.presentation_delta:
            payload["presentationDelta"] = dict(self.presentation_delta)
        if self.clarification is not None:
            payload["clarification"] = self.clarification.as_dict()
        return payload

    @classmethod
    def from_dict(cls, payload: dict[str, Any] | None) -> TurnRefinement | None:
        if not isinstance(payload, dict):
            return None
        kind = str(payload.get("kind") or "").strip().lower()
        if not kind:
            return None
        if kind not in SUPPORTED_REFINEMENT_KINDS:
            kind = "unknown"
        try:
            confidence = float(payload.get("confidence"))
        except (TypeError, ValueError):
            return None
        confidence = max(0.0, min(1.0, confidence))

        target_raw = payload.get("target")
        target = (
            TurnRefinementTarget.from_dict(target_raw)
            if isinstance(target_raw, dict)
            else None
        )

        presentation = payload.get("presentationDelta") or payload.get(
            "presentation_delta"
        )
        if presentation is not None and not isinstance(presentation, dict):
            presentation = None
        elif isinstance(presentation, dict):
            presentation = _strip_forbidden(presentation) or None

        cleared_raw = (
            payload.get("clearedArguments") or payload.get("cleared_arguments") or ()
        )
        cleared = tuple(
            str(item).strip()
            for item in cleared_raw
            if str(item or "").strip() and str(item).strip() not in FORBIDDEN_SEMANTIC_KEYS
        )

        conflicts_raw = payload.get("conflicts") or ()
        conflicts: list[TurnRefinementConflict] = []
        for item in conflicts_raw:
            conflict = TurnRefinementConflict.from_dict(
                item if isinstance(item, dict) else None
            )
            if conflict is not None:
                conflicts.append(conflict)

        version = payload.get("contractVersion") or payload.get("contract_version") or 1
        try:
            version_int = int(version)
        except (TypeError, ValueError):
            version_int = TURN_REFINEMENT_CONTRACT_VERSION

        return cls(
            kind=kind,
            confidence=confidence,
            target=target,
            argument_delta=_clean_argument_delta(
                payload.get("argumentDelta") or payload.get("argument_delta")
            ),
            cleared_arguments=cleared,
            presentation_delta=dict(presentation) if isinstance(presentation, dict) else None,
            clarification=TurnRefinementClarification.from_dict(
                payload.get("clarification")
                if isinstance(payload.get("clarification"), dict)
                else None
            ),
            conflicts=tuple(conflicts),
            reason=str(payload.get("reason") or "").strip(),
            source=str(payload.get("source") or "heuristic").strip() or "heuristic",
            contract_version=version_int,
        )

    @classmethod
    def fallback_clarify(
        cls,
        reason: str,
        *,
        prompt_hint: str | None = None,
        source: str = "fallback",
        confidence: float = 0.2,
    ) -> TurnRefinement:
        text = str(reason or "").strip() or "malformed_or_missing_contract"
        return cls(
            kind="clarify",
            confidence=max(0.0, min(1.0, float(confidence))),
            clarification=TurnRefinementClarification(
                reason=text,
                prompt_hint=prompt_hint,
            ),
            reason=text,
            source=source,
        )

    @classmethod
    def from_legacy_operational_refinement(
        cls,
        legacy: Any,
        *,
        inherited_arguments: dict[str, Any] | None = None,
        source: str = "legacy_operational_refinement",
    ) -> TurnRefinement:
        """Adapter shadow: mapeia OperationalRefinement legado sem promover path."""
        kind_raw = str(getattr(legacy, "kind", "") or "").strip().lower()
        action_id = str(getattr(legacy, "action_id", "") or "").strip() or None
        target = TurnRefinementTarget(
            kind="action" if action_id else "unknown",
            action_id=action_id,
        )

        delta: dict[str, Any] = {}
        for attr, key in (
            ("page", "page"),
            ("page_size", "page_size"),
            ("branch", "branch"),
            ("warehouse", "warehouse"),
            ("group_by", "group_by"),
            ("max_depth", "max_depth"),
            ("product_code", "product_code"),
        ):
            value = getattr(legacy, attr, None)
            if value is not None and value != "":
                delta[key] = value

        cleared: list[str] = []
        if bool(getattr(legacy, "clears_branch_filter", False)):
            cleared.append("branch")

        presentation: dict[str, Any] | None = None
        if kind_raw in {"format_refinement", "presentation_refinement"}:
            presentation = {"kind": kind_raw}

        contract_kind = "argument_delta"
        if presentation and not delta:
            contract_kind = "presentation_delta"
        elif not delta and not cleared:
            contract_kind = "no_op"

        conflicts: list[TurnRefinementConflict] = []
        inherited = _clean_argument_delta(inherited_arguments or {})
        for key, proposed in delta.items():
            if key in inherited and inherited[key] != proposed:
                conflicts.append(
                    TurnRefinementConflict(
                        argument=key,
                        inherited_value=inherited[key],
                        proposed_value=proposed,
                        resolution="explicit_wins",
                    )
                )

        return cls(
            kind=contract_kind,
            confidence=0.7 if delta or presentation else 0.4,
            target=target,
            argument_delta=delta,
            cleared_arguments=tuple(cleared),
            presentation_delta=presentation,
            conflicts=tuple(conflicts),
            reason=str(getattr(legacy, "reason", "") or "").strip(),
            source=source,
        )
