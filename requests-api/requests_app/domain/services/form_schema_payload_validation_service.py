"""Validate request payloads against RequestType.form_schema (JSON Schema subset).

Transversal — no type_code branching. Typed validators (e.g. invoice-issuance) take
precedence in PayloadValidatorRegistry.
"""

from __future__ import annotations

from typing import Any

from requests_app.application.errors import ApplicationError


class FormSchemaPayloadValidationService:
    """Minimal JSON Schema object validation (required, type, enum, minLength)."""

    def validate(self, payload: dict[str, Any], form_schema: dict[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, dict):
            raise ApplicationError(code="payload_required", status_code=422)
        schema = form_schema if isinstance(form_schema, dict) else {}
        properties = schema.get("properties")
        if not isinstance(properties, dict) or not properties:
            return dict(payload)

        required = schema.get("required") or []
        if not isinstance(required, list):
            required = []

        out: dict[str, Any] = {}
        allow_additional = schema.get("additionalProperties", True) is not False

        for key in required:
            field = str(key)
            if field not in payload or payload.get(field) in (None, ""):
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    field=field,
                    detail=f"Campo obrigatório ausente: {field}.",
                )

        for key, value in payload.items():
            field = str(key)
            prop = properties.get(field)
            if prop is None:
                if allow_additional:
                    out[field] = value
                    continue
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    field=field,
                    detail=f"Campo não permitido: {field}.",
                )
            out[field] = self._coerce_property(field, value, prop if isinstance(prop, dict) else {})

        for key in required:
            field = str(key)
            if field not in out:
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    field=field,
                    detail=f"Campo obrigatório ausente: {field}.",
                )
        return out

    def _coerce_property(self, field: str, value: Any, prop: dict[str, Any]) -> Any:
        expected = str(prop.get("type") or "string")
        if expected == "string":
            text = "" if value is None else str(value).strip()
            min_length = prop.get("minLength")
            if isinstance(min_length, int) and len(text) < min_length:
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    field=field,
                    detail=f"{field} é obrigatório.",
                )
            enum_values = prop.get("enum")
            if isinstance(enum_values, list) and enum_values and text not in enum_values:
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    field=field,
                    detail=f"{field} deve ser um de: {', '.join(str(v) for v in enum_values)}.",
                )
            return text
        if expected == "number" or expected == "integer":
            try:
                number = float(value) if expected == "number" else int(value)
            except (TypeError, ValueError) as exc:
                raise ApplicationError(
                    code="payload_invalid",
                    status_code=422,
                    field=field,
                    detail=f"{field} inválido.",
                ) from exc
            return number
        if expected == "boolean":
            if isinstance(value, bool):
                return value
            raise ApplicationError(
                code="payload_invalid",
                status_code=422,
                field=field,
                detail=f"{field} deve ser booleano.",
            )
        return value
