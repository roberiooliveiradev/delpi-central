# app/application/validators/manifest_validator.py

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from jsonschema import Draft202012Validator

from app.domain.plugins.manifest_rules import ManifestError, validate_manifest_rules


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    errors: List[ManifestError]


class ManifestValidator:
    """
    Validação em 2 etapas:
      1) JSON Schema (estrutura, tipos, required)
      2) Business rules (coerência e convenções)
    """

    def __init__(self, schema_path: Optional[str] = None) -> None:
        self._schema_path = schema_path or str(
            Path(__file__).resolve().parents[2]
            / "infrastructure"
            / "plugins"
            / "schemas"
            / "delpi.manifest.schema.json"
        )

        schema = self._load_schema()
        Draft202012Validator.check_schema(schema)
        self._validator = Draft202012Validator(schema)

    def _load_schema(self) -> Dict[str, Any]:
        with open(self._schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self, manifest: Dict[str, Any]) -> ValidationResult:
        errors: List[ManifestError] = []

        # 1) JSON Schema
        for e in sorted(self._validator.iter_errors(manifest), key=lambda x: list(x.path)):
            json_path = "$"
            for p in e.path:
                if isinstance(p, int):
                    json_path += f"[{p}]"
                else:
                    json_path += f".{p}"

            errors.append(
                ManifestError(
                    code="schema_validation_error",
                    message=e.message,
                    path=json_path,
                )
            )

        # evita cascata
        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        # 2) Business rules
        errors.extend(validate_manifest_rules(manifest))

        return ValidationResult(is_valid=(len(errors) == 0), errors=errors)