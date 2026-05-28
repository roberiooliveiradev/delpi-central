from __future__ import annotations

from si_app.infrastructure.persistence.plugins.repositories.strategic_indicators.postgres_admin_config_bundle_repository import (
    PostgresStrategicIndicatorsAdminConfigBundleRepository,
)


class ImportStrategicIndicatorsAdminConfigUseCase:
    def __init__(
        self,
        repository: PostgresStrategicIndicatorsAdminConfigBundleRepository,
    ) -> None:
        self._repository = repository

    def execute(
        self,
        *,
        bundle: dict,
        actor_user_id: str | None,
        include_goals: bool = True,
    ) -> dict:
        if not isinstance(bundle, dict):
            raise ValueError("Pacote de importação inválido.")

        stats = self._repository.import_bundle(
            bundle=bundle,
            actor_user_id=actor_user_id,
            include_goals=include_goals,
        )

        return {
            "message": "Configuração importada com sucesso.",
            "stats": stats,
        }
