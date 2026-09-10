"""E3.S5 — group-by/refetch guiado por schema OpenAPI + actionId (sem pathContains)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.domain.services.chat_message_normalization_service import (
    ChatMessageNormalizationService,
)
from app.domain.services.chat_operational_session_data_refinement_service import (
    ChatOperationalSessionDataRefinementService,
)


@dataclass(frozen=True)
class SchemaDrivenGroupByCapability:
    parameter_name: str
    enum_values: tuple[str, ...]
    default_value: str | None = None


@dataclass(frozen=True)
class SchemaDrivenGroupByPlan:
    action_id: str
    parameter_name: str
    dimension: str
    dimension_label: str
    execution_path: str
    parameters: dict[str, Any]
    refetch_group_by: str | None = None
    clarification_reason: str | None = None
    path: str | None = None  # observabilidade only — not a match key

    @property
    def ok(self) -> bool:
        return self.execution_path in {"session", "refetch"} and not self.clarification_reason


class SchemaDrivenGroupByRefinementService:
    """Deriva group_by do schema; identidade da action por actionId, não por path."""

    AGGREGATE_HINTS = (
        "agrup",
        "agrupar",
        "agrupamento",
        "ranking",
        "consumo por",
        "total por",
        "soma por",
        "somar por",
        "por filial",
        "por grupo",
        "por unidade",
    )

    @classmethod
    def extract_capability(cls, action: dict[str, Any] | None) -> SchemaDrivenGroupByCapability | None:
        if not isinstance(action, dict):
            return None
        schema_params = (
            action.get("parametersSchema") or action.get("parameters_schema") or []
        )
        if not isinstance(schema_params, list):
            return None

        preferred: dict[str, Any] | None = None
        fallback: dict[str, Any] | None = None
        for item in schema_params:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            if not name:
                continue
            schema = item.get("schema") if isinstance(item.get("schema"), dict) else {}
            enum_raw = schema.get("enum") if isinstance(schema, dict) else None
            if not isinstance(enum_raw, list) or not enum_raw:
                continue
            enum_values = tuple(
                str(value).strip() for value in enum_raw if str(value or "").strip()
            )
            if not enum_values:
                continue
            payload = {"name": name, "enum": enum_values, "schema": schema, "item": item}
            if name in {"group_by", "groupBy", "groupby"}:
                preferred = payload
                break
            if fallback is None:
                fallback = payload

        chosen = preferred or fallback
        if chosen is None:
            return None

        schema = chosen["schema"] if isinstance(chosen.get("schema"), dict) else {}
        default = schema.get("default")
        default_value = str(default).strip() if default is not None else None
        return SchemaDrivenGroupByCapability(
            parameter_name=str(chosen["name"]),
            enum_values=tuple(chosen["enum"]),
            default_value=default_value,
        )

    @classmethod
    def match_vocabulary_route_by_action_id(
        cls,
        action_id: str,
        routes: list[dict[str, Any]] | None,
    ) -> dict[str, Any] | None:
        target = str(action_id or "").strip().lower()
        if not target or not isinstance(routes, list):
            return None
        for route in routes:
            if not isinstance(route, dict):
                continue
            default_id = str(route.get("actionIdDefault") or "").strip().lower()
            route_action = str(route.get("actionId") or "").strip().lower()
            if target and target in {default_id, route_action}:
                return route
        return None

    @classmethod
    def resolve_dimension(
        cls,
        message: str,
        *,
        capability: SchemaDrivenGroupByCapability,
        vocabulary_route: dict[str, Any] | None = None,
    ) -> tuple[str | None, str]:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized:
            return None, ""

        # 1) Vocabulary terms (UX) mapped to enum values — not path-keyed.
        if isinstance(vocabulary_route, dict):
            matches: list[tuple[int, str, str]] = []
            for entry in vocabulary_route.get("dimensions") or []:
                if not isinstance(entry, dict):
                    continue
                value = str(entry.get("value") or "").strip()
                if value not in capability.enum_values:
                    continue
                label = str(entry.get("label") or value).strip()
                terms = entry.get("terms") or []
                if not isinstance(terms, list):
                    continue
                for term in terms:
                    token = str(term or "").strip().lower()
                    if token and token in normalized:
                        matches.append((len(token), value, label))
            if matches:
                matches.sort(key=lambda item: item[0], reverse=True)
                return matches[0][1], matches[0][2]

        # 2) Direct enum / humanized enum match.
        matches_enum: list[tuple[int, str]] = []
        for value in capability.enum_values:
            lowered = value.lower()
            humanized = lowered.replace("_", " ")
            for token in (lowered, humanized):
                if token and token in normalized:
                    matches_enum.append((len(token), value))
            # compact form without separators
            compact = lowered.replace("_", "")
            if compact and len(compact) >= 4 and compact in normalized.replace(" ", ""):
                matches_enum.append((len(compact), value))
        if matches_enum:
            matches_enum.sort(key=lambda item: item[0], reverse=True)
            value = matches_enum[0][1]
            return value, value.replace("_", " ")

        return None, ""

    @classmethod
    def looks_like_group_by_request(cls, message: str) -> bool:
        normalized = ChatMessageNormalizationService.normalize_for_matching(message)
        if not normalized:
            return False
        return any(hint in normalized for hint in cls.AGGREGATE_HINTS)

    @classmethod
    def resolve_execution_path(
        cls,
        *,
        dimension: str,
        vocabulary_route: dict[str, Any] | None,
        rows: list[dict[str, Any]] | None,
        capability: SchemaDrivenGroupByCapability,
    ) -> tuple[str, str | None]:
        if dimension not in capability.enum_values:
            return "clarify", None

        dimension_entry: dict[str, Any] = {}
        if isinstance(vocabulary_route, dict):
            dimension_entry = ChatOperationalSessionDataRefinementService.dimension_config(
                vocabulary_route,
                dimension,
            )

        if dimension_entry:
            path = ChatOperationalSessionDataRefinementService.resolve_execution_path(
                dimension_entry,
                list(rows or []),
            )
            if path == "skip":
                return "clarify", None
            refetch = None
            if path == "refetch":
                refetch = ChatOperationalSessionDataRefinementService.refetch_group_by_value(
                    dimension_entry,
                    dimension=dimension,
                )
            return path, refetch

        # Schema-only: refetch when enum accepts; session if rows expose the field.
        if cls._rows_support_dimension(rows or [], dimension):
            return "session", None
        return "refetch", dimension

    @classmethod
    def plan(
        cls,
        message: str,
        *,
        action: dict[str, Any],
        action_id: str,
        previous_parameters: dict[str, Any] | None = None,
        rows: list[dict[str, Any]] | None = None,
        vocabulary_routes: list[dict[str, Any]] | None = None,
        path: str | None = None,
    ) -> SchemaDrivenGroupByPlan:
        capability = cls.extract_capability(action)
        action_key = str(action_id or "").strip()
        params = dict(previous_parameters or {})

        if capability is None:
            return SchemaDrivenGroupByPlan(
                action_id=action_key,
                parameter_name="group_by",
                dimension="",
                dimension_label="",
                execution_path="clarify",
                parameters=params,
                clarification_reason="action_has_no_group_by_parameter",
                path=path,
            )

        if not cls.looks_like_group_by_request(message):
            return SchemaDrivenGroupByPlan(
                action_id=action_key,
                parameter_name=capability.parameter_name,
                dimension="",
                dimension_label="",
                execution_path="clarify",
                parameters=params,
                clarification_reason="message_not_group_by_refinement",
                path=path,
            )

        vocabulary = cls.match_vocabulary_route_by_action_id(
            action_key,
            vocabulary_routes,
        )
        dimension, label = cls.resolve_dimension(
            message,
            capability=capability,
            vocabulary_route=vocabulary,
        )
        if not dimension:
            return SchemaDrivenGroupByPlan(
                action_id=action_key,
                parameter_name=capability.parameter_name,
                dimension="",
                dimension_label="",
                execution_path="clarify",
                parameters=params,
                clarification_reason="dimension_not_resolved",
                path=path,
            )

        current = str(params.get(capability.parameter_name) or capability.default_value or "").strip()
        if current.lower() == dimension.lower():
            return SchemaDrivenGroupByPlan(
                action_id=action_key,
                parameter_name=capability.parameter_name,
                dimension=dimension,
                dimension_label=label or dimension,
                execution_path="clarify",
                parameters=params,
                clarification_reason="dimension_unchanged",
                path=path,
            )

        execution_path, refetch = cls.resolve_execution_path(
            dimension=dimension,
            vocabulary_route=vocabulary,
            rows=rows,
            capability=capability,
        )
        if execution_path == "clarify":
            return SchemaDrivenGroupByPlan(
                action_id=action_key,
                parameter_name=capability.parameter_name,
                dimension=dimension,
                dimension_label=label or dimension,
                execution_path="clarify",
                parameters=params,
                clarification_reason="dimension_not_executable",
                path=path,
            )

        return SchemaDrivenGroupByPlan(
            action_id=action_key,
            parameter_name=capability.parameter_name,
            dimension=dimension,
            dimension_label=label or dimension,
            execution_path=execution_path,
            parameters=params,
            refetch_group_by=refetch,
            path=path,
        )

    @classmethod
    def _rows_support_dimension(cls, rows: list[dict[str, Any]], dimension: str) -> bool:
        if not rows:
            return False
        field = dimension
        aliases = {
            "branch_summary": "branch",
            "product_group": "product_group",
            "unit": "unit",
        }
        field = aliases.get(dimension, dimension)
        sample = rows[0] if isinstance(rows[0], dict) else {}
        return field in sample
