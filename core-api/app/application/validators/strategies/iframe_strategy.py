# api/app/application/validators/strategies/iframe_strategy.py

from typing import Dict, List
from app.domain.plugins.manifest_rules import ManifestError
from app.application.validators.strategies.manifest_strategy import ManifestValidationStrategy


class IframeStrategy(ManifestValidationStrategy):
    """
    Validação específica para plugins do tipo 'iframe'.

    Responsável apenas por regras semânticas adicionais
    além do JSON Schema.
    """

    def validate(self, manifest: Dict) -> List[ManifestError]:
        errors: List[ManifestError] = []

        entry = str(manifest.get("entry") or "").strip()
        routes = manifest.get("routes") or []

        # --------------------------------------------------
        # entry obrigatório
        # --------------------------------------------------
        if not entry:
            errors.append(
                ManifestError(
                    code="entry_required",
                    message="Campo 'entry' é obrigatório para plugins do tipo 'iframe'.",
                    path="$.entry",
                )
            )
        else:
            if not entry.startswith("http://") and not entry.startswith("https://"):
                errors.append(
                    ManifestError(
                        code="invalid_iframe_entry_url",
                        message="Para plugins iframe, 'entry' deve iniciar com http:// ou https://.",
                        path="$.entry",
                    )
                )

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

        return errors