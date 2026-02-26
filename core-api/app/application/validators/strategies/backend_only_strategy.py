# strategies/backend_only_strategy.py

from typing import Dict, List
from app.domain.plugins.manifest_rules import ManifestError
from app.application.validators.strategies.manifest_strategy import ManifestValidationStrategy


class BackendOnlyStrategy(ManifestValidationStrategy):

    def validate(self, manifest: Dict) -> List[ManifestError]:
        errors: List[ManifestError] = []

        backend = manifest.get("backend") or {}

        if backend.get("required") is not True:
            errors.append(
                ManifestError(
                    code="backend_required_must_be_true",
                    message="backend.required deve ser true para backend-only.",
                    path="$.backend.required",
                )
            )

        if backend.get("validateJwt") is True:
            if not backend.get("issuer"):
                errors.append(
                    ManifestError(
                        code="missing_issuer",
                        message="issuer é obrigatório quando validateJwt=true.",
                        path="$.backend.issuer",
                    )
                )

            if not backend.get("audience"):
                errors.append(
                    ManifestError(
                        code="missing_audience",
                        message="audience é obrigatório quando validateJwt=true.",
                        path="$.backend.audience",
                    )
                )

        return errors