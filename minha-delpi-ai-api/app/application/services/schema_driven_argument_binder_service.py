"""E3.S4 — schema-driven argument binder over TurnRefinement + OpenAPI action schema.

Combines inherited context, explicit argument delta and deterministic coercion/validation.
Does not invent required values. Does not use path/operationId as semantic keys.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from app.application.services.validate_action_arguments_service import (
    ValidateActionArgumentsService,
)
from app.domain.entities.turn_refinement import TurnRefinement
from app.domain.services.chat_openapi_argument_coercion_service import (
    ChatOpenApiArgumentCoercionService,
)
from app.domain.services.chat_tool_parameter_grounding_service import (
    ChatToolParameterGroundingService,
)
from app.domain.services.turn_refinement_validator_service import (
    TurnRefinementValidatorService,
)


@dataclass(frozen=True)
class SchemaDrivenBindResult:
    ok: bool
    parameters: dict[str, Any] = field(default_factory=dict)
    body: dict[str, Any] | None = None
    missing: tuple[str, ...] = ()
    errors: tuple[str, ...] = ()
    conflicts: tuple[dict[str, Any], ...] = ()
    clarification_reason: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "parameters": dict(self.parameters),
            "body": dict(self.body) if isinstance(self.body, dict) else self.body,
            "missing": list(self.missing),
            "errors": list(self.errors),
            "conflicts": list(self.conflicts),
            "clarificationReason": self.clarification_reason,
        }


class SchemaDrivenArgumentBinderService:
    """OpenAPI parameters/requestBody as authority for refinement deltas."""

    def __init__(
        self,
        validator: ValidateActionArgumentsService | None = None,
    ) -> None:
        self._validator = validator or ValidateActionArgumentsService()

    @classmethod
    def bind(
        cls,
        *,
        action: dict[str, Any],
        refinement: TurnRefinement | dict[str, Any] | None,
        inherited_parameters: dict[str, Any] | None = None,
        inherited_body: dict[str, Any] | None = None,
        message: str | None = None,
        previous_messages: list | None = None,
        provider: dict[str, Any] | None = None,
    ) -> SchemaDrivenBindResult:
        return cls().bind_instance(
            action=action,
            refinement=refinement,
            inherited_parameters=inherited_parameters,
            inherited_body=inherited_body,
            message=message,
            previous_messages=previous_messages,
            provider=provider,
        )

    def bind_instance(
        self,
        *,
        action: dict[str, Any],
        refinement: TurnRefinement | dict[str, Any] | None,
        inherited_parameters: dict[str, Any] | None = None,
        inherited_body: dict[str, Any] | None = None,
        message: str | None = None,
        previous_messages: list | None = None,
        provider: dict[str, Any] | None = None,
    ) -> SchemaDrivenBindResult:
        ensured = TurnRefinementValidatorService.ensure(
            refinement,
            inherited_arguments=inherited_parameters,
            fallback_reason="refinement_missing",
        )
        if ensured.kind == "clarify" and not ensured.argument_delta:
            return SchemaDrivenBindResult(
                ok=False,
                clarification_reason=(
                    ensured.clarification.reason
                    if ensured.clarification is not None
                    else ensured.reason or "needs_clarification"
                ),
                errors=("clarify",),
                conflicts=tuple(item.as_dict() for item in ensured.conflicts),
            )

        schema_params = _schema_params(action)
        declared_names = {
            str(item.get("name"))
            for item in schema_params
            if isinstance(item, dict) and item.get("name")
        }

        merged = dict(inherited_parameters or {})
        for key in ensured.cleared_arguments:
            merged.pop(key, None)
        merged.update(
            {
                key: value
                for key, value in ensured.argument_delta.items()
                if key != "body"
            }
        )

        parameters = ChatToolParameterGroundingService.retain_declared_parameters(
            schema_params,
            merged,
        )
        # If schema is empty, refuse to invent params (OpenAPI authority).
        if not declared_names:
            parameters = {}

        parameters = ChatOpenApiArgumentCoercionService.coerce_parameters(
            parameters,
            schema_params,
            message=str(message or ""),
            previous_messages=previous_messages,
        )

        parameters = _coerce_integer_strings(parameters, schema_params)

        body = None
        body_delta = ensured.argument_delta.get("body")
        if isinstance(body_delta, dict):
            body = dict(inherited_body or {})
            body.update(body_delta)
        elif isinstance(inherited_body, dict) and inherited_body:
            body = dict(inherited_body)

        presentation_only = (
            ensured.kind == "presentation_delta" and not ensured.argument_delta
        )
        if presentation_only:
            return SchemaDrivenBindResult(
                ok=True,
                parameters=parameters,
                body=body,
                conflicts=tuple(item.as_dict() for item in ensured.conflicts),
            )

        arguments: dict[str, Any] = {"parameters": parameters}
        if body is not None:
            arguments["body"] = body

        normalized, error = self._validator.try_validate(
            provider=provider or {"enabled": True},
            action=_normalize_action_schema_keys(action),
            arguments=arguments,
        )
        if error is not None:
            missing = ()
            if getattr(error, "missing_parameter", None):
                missing = tuple(
                    part.strip()
                    for part in str(error.missing_parameter).split(",")
                    if part.strip()
                )
            return SchemaDrivenBindResult(
                ok=False,
                parameters=parameters,
                body=body,
                missing=missing,
                errors=(str(getattr(error, "error_kind", None) or "validation_error"),),
                conflicts=tuple(item.as_dict() for item in ensured.conflicts),
                clarification_reason=str(error),
            )

        assert normalized is not None
        return SchemaDrivenBindResult(
            ok=True,
            parameters=dict(normalized.get("parameters") or {}),
            body=(
                dict(normalized["body"])
                if isinstance(normalized.get("body"), dict)
                else normalized.get("body")
            ),
            conflicts=tuple(item.as_dict() for item in ensured.conflicts),
        )


def _schema_params(action: dict[str, Any]) -> list[dict[str, Any]]:
    raw = action.get("parametersSchema") or action.get("parameters_schema") or []
    return [item for item in raw if isinstance(item, dict)]


def _normalize_action_schema_keys(action: dict[str, Any]) -> dict[str, Any]:
    """Policy reads camelCase; accept snake_case fixtures."""
    payload = dict(action)
    if "parametersSchema" not in payload and "parameters_schema" in payload:
        payload["parametersSchema"] = payload["parameters_schema"]
    if "requestBodySchema" not in payload and "request_body_schema" in payload:
        payload["requestBodySchema"] = payload["request_body_schema"]
    payload.setdefault("enabled", True)
    payload.setdefault("path", payload.get("path") or "/")
    payload.setdefault("method", payload.get("method") or "GET")
    return payload


def _coerce_integer_strings(
    parameters: dict[str, Any],
    schema_params: list[dict[str, Any]],
) -> dict[str, Any]:
    out = dict(parameters)
    by_name = {
        str(item.get("name")): item
        for item in schema_params
        if isinstance(item, dict) and item.get("name")
    }
    for name, value in list(out.items()):
        parameter = by_name.get(name)
        if not parameter:
            continue
        schema = parameter.get("schema") if isinstance(parameter.get("schema"), dict) else {}
        expected = str(schema.get("type") or parameter.get("type") or "").strip().lower()
        if expected in {"integer", "int"} and isinstance(value, str) and value.isdigit():
            out[name] = int(value)
    return out
