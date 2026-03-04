# app/application/validators/strategies/microfrontend_strategy.py

from typing import Dict, List
from app.domain.plugins.manifest_rules import ManifestError
from app.application.validators.strategies.manifest_strategy import ManifestValidationStrategy


class MicrofrontendStrategy(ManifestValidationStrategy):

    def validate(self, manifest: Dict) -> List[ManifestError]:
        errors: List[ManifestError] = []

        entry = manifest.get("entry")
        routes = manifest.get("routes") or []

        # --------------------------------------------------
        # routes obrigatórias
        # --------------------------------------------------
        if not routes:
            errors.append(
                ManifestError(
                    code="routes_required",
                    message="routes são obrigatórias para microfrontend.",
                    path="$.routes",
                )
            )

        # --------------------------------------------------
        # entry global OU route.entry
        # --------------------------------------------------
        if not entry:
            missing_entry_routes = []

            for i, route in enumerate(routes):
                if not route.get("entry"):
                    missing_entry_routes.append(i)

            if missing_entry_routes:
                errors.append(
                    ManifestError(
                        code="entry_required",
                        message="entry global ou routes[].entry é obrigatório para microfrontend.",
                        path="$.entry",
                    )
                )

        return errors