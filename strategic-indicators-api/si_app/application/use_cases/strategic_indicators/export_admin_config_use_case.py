from __future__ import annotations

from si_app.application.services.strategic_indicators.admin_config_bundle_service import (
    AdminConfigBundleService,
)


class ExportStrategicIndicatorsAdminConfigUseCase:
    def __init__(self, service: AdminConfigBundleService) -> None:
        self._service = service

    def execute(self, *, actor_user_id: str | None = None) -> dict:
        return self._service.export(actor_user_id=actor_user_id)
