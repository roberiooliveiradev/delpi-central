from __future__ import annotations

from si_app.application.services.strategic_indicators.admin_config_bundle_service import (
    AdminConfigBundleService,
)


class PreviewStrategicIndicatorsAdminConfigUseCase:
    def __init__(self, service: AdminConfigBundleService) -> None:
        self._service = service

    def execute(
        self,
        *,
        bundle: dict,
        mode: str = "replace",
        include_goals: bool = True,
    ) -> dict:
        if mode not in ("merge", "replace"):
            raise ValueError("mode inválido: use merge ou replace.")
        return self._service.preview(
            bundle=bundle,
            mode=mode,
            include_goals=include_goals,
        )
