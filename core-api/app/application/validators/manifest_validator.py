# app/application/validators/manifest_validator.py
import json
from pathlib import Path
from typing import Any, Dict, List

from jsonschema import Draft202012Validator

from app.domain.plugins.manifest_rules import (
    ManifestError,
    validate_manifest_rules,
)

from app.application.validators.validation_result import ValidationResult
from app.application.validators.manifest_version_resolver import ManifestVersionResolver
from app.application.validators.manifest_normalizer import ManifestNormalizer
from app.application.validators.strategies.backend_only_strategy import BackendOnlyStrategy
from app.application.validators.strategies.microfrontend_strategy import MicrofrontendStrategy
from app.application.validators.strategies.iframe_strategy import IframeStrategy


class ManifestValidator:

    def __init__(self, schema_path: str | None = None) -> None:
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

        # 1. Normalização automática
        manifest = ManifestNormalizer.normalize(manifest)

        # 2. Resolver versão
        ManifestVersionResolver.resolve(manifest)

        errors: List[ManifestError] = []

        # 3. JSON Schema
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

        if errors:
            return ValidationResult(False, errors)

        # 4. Strategy por tipo
        plugin_type = manifest.get("type")

        if plugin_type == "backend-only":
            strategy = BackendOnlyStrategy()
        elif plugin_type == "microfrontend":
            strategy = MicrofrontendStrategy()
        elif plugin_type == "iframe":
            strategy = IframeStrategy()
        else:
            return ValidationResult(
                False,
                [
                    ManifestError(
                        code="unsupported_plugin_type",
                        message=f"Tipo de plugin '{plugin_type}' não suportado.",
                        path="$.type",
                    )
                ],
            )

        errors.extend(strategy.validate(manifest))

        # 5. Regras de domínio
        errors.extend(validate_manifest_rules(manifest))

        return ValidationResult(len(errors) == 0, errors)