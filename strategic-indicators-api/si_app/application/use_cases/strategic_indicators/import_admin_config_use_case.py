from __future__ import annotations

from si_app.application.services.strategic_indicators.admin_config_bundle_service import (
    AdminConfigBundleService,
)


class ImportStrategicIndicatorsAdminConfigUseCase:
    def __init__(self, service: AdminConfigBundleService) -> None:
        self._service = service

    def execute(
        self,
        *,
        bundle: dict,
        actor_user_id: str | None,
        include_goals: bool = True,
        mode: str = "replace",
    ) -> dict:
        if mode not in ("merge", "replace"):
            raise ValueError("mode inválido: use merge ou replace.")
        stats = self._service.apply(
            bundle=bundle,
            actor_user_id=actor_user_id,
            include_goals=include_goals,
            mode=mode,
        )
        return {
            "message": "Configuração importada com sucesso.",
            "stats": stats,
        }
