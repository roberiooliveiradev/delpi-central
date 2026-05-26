from si_app.domain.ports.strategic_indicators.change_request_repository_port import (
    StrategicIndicatorsChangeRequestRepositoryPort,
)


class SubmitStrategicIndicatorsChangeRequestUseCase:
    def __init__(self, repository: StrategicIndicatorsChangeRequestRepositoryPort):
        self._repository = repository

    def execute(
        self,
        change_request_id: str,
        actor_user_id: str | None,
    ) -> dict:
        return self._repository.submit_change_request(
            change_request_id=change_request_id,
            actor_user_id=actor_user_id,
        )