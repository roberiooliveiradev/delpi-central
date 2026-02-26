# app/application/validators/strategies/microfrontend_strategy.py

from typing import Dict, List
from app.domain.plugins.manifest_rules import ManifestError
from app.application.validators.strategies.manifest_strategy import ManifestValidationStrategy


class MicrofrontendStrategy(ManifestValidationStrategy):

    def validate(self, manifest: Dict) -> List[ManifestError]:
        errors: List[ManifestError] = []

        if not manifest.get("entry"):
            errors.append(
                ManifestError(
                    code="entry_required",
                    message="entry é obrigatório para microfrontend.",
                    path="$.entry",
                )
            )

        if not manifest.get("routes"):
            errors.append(
                ManifestError(
                    code="routes_required",
                    message="routes são obrigatórias para microfrontend.",
                    path="$.routes",
                )
            )

        return errors