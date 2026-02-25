# app/application/plugins/manifest_validator.py

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
    def __init__(self, schema_path: Optional[str] = None) -> None:
        self._schema_path = schema_path or str(
            Path(__file__).resolve().parents[2] / "infrastructure" / "plugins" / "schemas" / "delpi.manifest.schema.json"
        )
        schema = self._load_schema()
        Draft202012Validator.check_schema(schema)
        self._validator = Draft202012Validator(schema)

    def _load_schema(self) -> Dict[str, Any]:
        with open(self._schema_path, "r", encoding="utf-8") as f:
            return json.load(f)

    def validate(self, manifest: Dict[str, Any]) -> ValidationResult:
        errors: List[ManifestError] = []
        if not isinstance(manifest, dict):
            return ValidationResult(
                is_valid=False,
                errors=[ManifestError(
                    code="invalid_manifest_type",
                    message="Manifest must be a JSON object",
                    path="$"
                )]
            )

        # 1) JSON Schema
        for e in sorted(self._validator.iter_errors(manifest), key=lambda x: x.path):
            json_path = "$"
            for p in e.path:
                if isinstance(p, int):
                    json_path += f"[{p}]"
                else:
                    json_path += f".{p}"

            errors.append(ManifestError(
                code="schema_validation_error",
                message=e.message,
                path=json_path,
            ))

        # Se schema já falhou, ainda podemos adicionar rules? (padrão: sim, mas evita cascata)
        # Aqui: só roda rules se schema passou, para evitar falso-positivo.
        if errors:
            return ValidationResult(is_valid=False, errors=errors)

        # 2) Business rules
        rule_errors = validate_manifest_rules(manifest)
        errors.extend(rule_errors)

        return ValidationResult(is_valid=len(errors) == 0, errors=errors)