from si_app.domain.ports.strategic_indicators.change_request_repository_port import (
    StrategicIndicatorsChangeRequestRepositoryPort,
)


class ListStrategicIndicatorsChangeRequestsUseCase:
    def __init__(self, repository: StrategicIndicatorsChangeRequestRepositoryPort):
        self._repository = repository

    def execute(self) -> list[dict]:
        return self._repository.list_change_requests()