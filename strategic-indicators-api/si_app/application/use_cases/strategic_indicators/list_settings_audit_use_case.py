from si_app.domain.ports.strategic_indicators.settings_audit_repository_port import (
    StrategicIndicatorsSettingsAuditRepositoryPort,
)


class ListStrategicIndicatorsSettingsAuditUseCase:
    def __init__(self, repository: StrategicIndicatorsSettingsAuditRepositoryPort):
        self._repository = repository

    def execute(
        self,
        *,
        limit: int = 20,
        entity_key: str | None = None,
    ) -> list[dict]:
        return self._repository.list_recent_events(
            limit=limit,
            entity_key=entity_key,
        )