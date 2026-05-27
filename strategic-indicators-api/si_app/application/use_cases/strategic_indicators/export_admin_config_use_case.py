from __future__ import annotations

from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_config_bundle_repository import (
    PostgresStrategicIndicatorsAdminConfigBundleRepository,
)


class ExportStrategicIndicatorsAdminConfigUseCase:
    def __init__(
        self,
        repository: PostgresStrategicIndicatorsAdminConfigBundleRepository,
    ) -> None:
        self._repository = repository

    def execute(self) -> dict:
        return self._repository.export_bundle()
