from si_app.domain.ports.strategic_indicators.change_request_repository_port import (
    StrategicIndicatorsChangeRequestRepositoryPort,
)


class ListStrategicIndicatorsChangeRequestsUseCase:
    def __init__(self, repository: StrategicIndicatorsChangeRequestRepositoryPort):
        self._repository = repository

    def execute(
        self,
        *,
        limit: int | None = None,
        offset: int = 0,
    ) -> tuple[list[dict], int]:
        return self._repository.list_change_requests(
            limit=limit,
            offset=offset,
        )