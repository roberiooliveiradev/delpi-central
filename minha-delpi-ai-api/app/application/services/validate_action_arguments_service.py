"""Validação determinística de argumentos contra o contrato OpenAPI da action."""

from __future__ import annotations

from typing import Any

from app.domain.exceptions.external_action_exceptions import ExternalActionValidationError
from app.domain.services.external_actions.external_action_execution_policy import (
    ExternalActionExecutionPolicy,
)


class ValidateActionArgumentsService:
    """Estende a policy com type/enum/format e rejeita valores inventados sem schema.default."""

    def __init__(self, policy: ExternalActionExecutionPolicy | None = None) -> None:
        self.policy = policy or ExternalActionExecutionPolicy()

    def validate(
        self,
        *,
        provider: dict[str, Any] | None,
        action: dict[str, Any],
        arguments: dict[str, Any],
    ) -> dict[str, Any]:
        provider_payload = provider or {"enabled": True}
        normalized = self._normalize_arguments(arguments)
        self.policy.validate(provider_payload, action, normalized)
        self._validate_parameter_types(action, normalized.get("parameters") or {})
        self._validate_body_schema(action, normalized.get("body"))
        return normalized

    def try_validate(
        self,
        *,
        provider: dict[str, Any] | None,
        action: dict[str, Any],
        arguments: dict[str, Any],
    ) -> tuple[dict[str, Any] | None, ExternalActionValidationError | None]:
        try:
            return self.validate(provider=provider, action=action, arguments=arguments), None
        except ExternalActionValidationError as exc:
            return None, exc
        except ValueError as exc:
            return None, ExternalActionValidationError(str(exc), error_kind="validation_error")

    @classmethod
    def _normalize_arguments(cls, arguments: dict[str, Any]) -> dict[str, Any]:
        payload = dict(arguments or {})
        parameters = payload.get("parameters")
        if parameters is None:
            payload["parameters"] = {}
        elif not isinstance(parameters, dict):
            raise ExternalActionValidationError(
                "parameters must be an object",
                error_kind="invalid_parameters",
            )
        return payload

    def _validate_parameter_types(self, action: dict[str, Any], parameters: dict[str, Any]) -> None:
        schema_params = {
            str(item.get("name")): item
            for item in (action.get("parametersSchema") or action.get("parameters_schema") or [])
            if isinstance(item, dict) and item.get("name")
        }
        for name, value in parameters.items():
            parameter = schema_params.get(str(name))
            if not parameter:
                continue
            schema = parameter.get("schema") if isinstance(parameter.get("schema"), dict) else {}
            enum_values = schema.get("enum") if isinstance(schema, dict) else None
            if isinstance(enum_values, list) and enum_values:
                allowed = {str(item) for item in enum_values}
                if str(value) not in allowed:
                    raise ExternalActionValidationError(
                        f"Invalid enum value for parameter: {name}",
                        error_kind="invalid_enum",
                        parameter_name=str(name),
                    )
            expected = str(schema.get("type") or parameter.get("type") or "").strip().lower()
            if expected and not self._value_matches_type(value, expected):
                raise ExternalActionValidationError(
                    f"Invalid type for parameter: {name}",
                    error_kind="invalid_type",
                    parameter_name=str(name),
                )

    def _validate_body_schema(self, action: dict[str, Any], body: Any) -> None:
        body_schema = action.get("requestBodySchema") or action.get("request_body_schema")
        if not isinstance(body_schema, dict):
            return
        required = self._required_body_properties(body_schema)
        if not required:
            return
        if not isinstance(body, dict):
            raise ExternalActionValidationError(
                "Missing request body",
                error_kind="missing_required_parameter",
                missing_parameter=",".join(required),
            )
        for name in required:
            if name not in body:
                raise ExternalActionValidationError(
                    f"Missing required body field: {name}",
                    error_kind="missing_required_parameter",
                    missing_parameter=str(name),
                )
        properties = self._body_properties(body_schema)
        additional = properties.get("additionalProperties", True)
        if additional is False:
            allowed = set(properties.get("properties") or {})
            for key in body:
                if key not in allowed:
                    raise ExternalActionValidationError(
                        f"Unknown body property: {key}",
                        error_kind="unknown_parameter",
                        parameter_name=str(key),
                    )

    @classmethod
    def _required_body_properties(cls, body_schema: dict[str, Any]) -> list[str]:
        schema = cls._json_schema(body_schema)
        required = schema.get("required") or []
        return [str(item) for item in required if str(item).strip()]

    @classmethod
    def _body_properties(cls, body_schema: dict[str, Any]) -> dict[str, Any]:
        return cls._json_schema(body_schema)

    @classmethod
    def _json_schema(cls, body_schema: dict[str, Any]) -> dict[str, Any]:
        content = body_schema.get("content")
        if isinstance(content, dict):
            for media in content.values():
                if isinstance(media, dict) and isinstance(media.get("schema"), dict):
                    return media["schema"]
        if isinstance(body_schema.get("schema"), dict):
            return body_schema["schema"]
        return body_schema if body_schema.get("type") or body_schema.get("properties") else {}

    @classmethod
    def _value_matches_type(cls, value: Any, expected: str) -> bool:
        if expected in {"string"}:
            return isinstance(value, str) or value is not None
        if expected in {"integer", "int"}:
            if isinstance(value, bool):
                return False
            if isinstance(value, int):
                return True
            if isinstance(value, str) and value.isdigit():
                return True
            return False
        if expected in {"number", "float"}:
            try:
                float(value)
                return not isinstance(value, bool)
            except (TypeError, ValueError):
                return False
        if expected == "boolean":
            return isinstance(value, bool) or str(value).lower() in {"true", "false", "0", "1"}
        if expected == "array":
            return isinstance(value, list)
        if expected == "object":
            return isinstance(value, dict)
        return True
