# api/app/application/validators/strategies/iframe_strategy.py
from typing import Dict, List
from app.domain.plugins.manifest_rules import ManifestError
from app.application.validators.strategies.manifest_strategy import ManifestValidationStrategy


class IframeStrategy(ManifestValidationStrategy):

    def validate(self, manifest: Dict) -> List[ManifestError]:
        errors: List[ManifestError] = []

        entry = str(manifest.get("entry") or "").strip()
        routes = manifest.get("routes") or []

        # --------------------------------------------------
        # routes obrigatórias
        # --------------------------------------------------
        if not routes:
            errors.append(
                ManifestError(
                    code="routes_required",
                    message="Plugins do tipo 'iframe' devem declarar ao menos uma route.",
                    path="$.routes",
                )
            )

        # --------------------------------------------------
        # valida entry global
        # --------------------------------------------------
        if entry:
            if not entry.startswith("http://") and not entry.startswith("https://"):
                errors.append(
                    ManifestError(
                        code="invalid_iframe_entry_url",
                        message="entry deve iniciar com http:// ou https://.",
                        path="$.entry",
                    )
                )

        # --------------------------------------------------
        # valida routes[].entry
        # --------------------------------------------------
        if not entry:
            missing_entry_routes = []

            for i, route in enumerate(routes):
                route_entry = str(route.get("entry") or "").strip()

                if not route_entry:
                    missing_entry_routes.append(i)
                    continue

                if not route_entry.startswith("http://") and not route_entry.startswith("https://"):
                    errors.append(
                        ManifestError(
                            code="invalid_iframe_entry_url",
                            message="routes[].entry deve iniciar com http:// ou https://.",
                            path=f"$.routes[{i}].entry",
                        )
                    )

            if missing_entry_routes:
                errors.append(
                    ManifestError(
                        code="entry_required",
                        message="entry global ou routes[].entry é obrigatório.",
                        path="$.entry",
                    )
                )

        return errors