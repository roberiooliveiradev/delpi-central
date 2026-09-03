from __future__ import annotations

from collections.abc import Mapping

from requests_app.domain.ports.payload_validator_port import PayloadValidatorPort


class PayloadValidatorRegistry:
    def __init__(self, validators: Mapping[str, PayloadValidatorPort] | None = None) -> None:
        self._by_code = {str(k): v for k, v in (validators or {}).items()}

    def register(self, validator: PayloadValidatorPort) -> None:
        self._by_code[str(validator.type_code)] = validator

    def get(self, type_code: str) -> PayloadValidatorPort | None:
        return self._by_code.get(str(type_code or "").strip())

    def validate(self, type_code: str, payload: dict) -> dict:
        validator = self.get(type_code)
        if validator is None:
            return payload
        return validator.validate(payload)
