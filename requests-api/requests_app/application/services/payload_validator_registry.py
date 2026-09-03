from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from requests_app.domain.ports.payload_validator_port import PayloadValidatorPort
from requests_app.domain.services.form_schema_payload_validation_service import (
    FormSchemaPayloadValidationService,
)


class PayloadValidatorRegistry:
    def __init__(
        self,
        validators: Mapping[str, PayloadValidatorPort] | None = None,
        *,
        form_schema_validator: FormSchemaPayloadValidationService | None = None,
    ) -> None:
        self._by_code = {str(k): v for k, v in (validators or {}).items()}
        self._form_schema = form_schema_validator or FormSchemaPayloadValidationService()

    def register(self, validator: PayloadValidatorPort) -> None:
        self._by_code[str(validator.type_code)] = validator

    def get(self, type_code: str) -> PayloadValidatorPort | None:
        return self._by_code.get(str(type_code or "").strip())

    def validate(
        self,
        type_code: str,
        payload: dict,
        *,
        form_schema: dict[str, Any] | None = None,
    ) -> dict:
        validator = self.get(type_code)
        if validator is not None:
            return validator.validate(payload)
        if isinstance(form_schema, dict) and form_schema.get("properties"):
            return self._form_schema.validate(payload, form_schema)
        return payload
