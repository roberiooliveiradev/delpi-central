from app.application.dto.strategic_indicators.create_change_request_request import (
    CreateStrategicIndicatorsChangeRequestRequest,
)
from app.domain.ports.strategic_indicators.change_request_repository_port import (
    StrategicIndicatorsChangeRequestRepositoryPort,
)


class CreateStrategicIndicatorsChangeRequestUseCase:
    VALID_BLOCKS = {
        "departments",
        "department_indicators",
        "indicator_goals",
        "parameters.global",
        "governance.notes",
    }

    def __init__(self, repository: StrategicIndicatorsChangeRequestRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: CreateStrategicIndicatorsChangeRequestRequest,
    ) -> dict:
        if not request.title.strip():
            raise ValueError("title é obrigatório.")

        if not request.description.strip():
            raise ValueError("description é obrigatório.")

        if request.target_block not in self.VALID_BLOCKS:
            raise ValueError("target_block inválido.")

        return self._repository.create_change_request(
            title=request.title.strip(),
            description=request.description.strip(),
            target_block=request.target_block,
            proposed_payload=request.proposed_payload,
            actor_user_id=request.actor_user_id,
            actor_email=request.actor_email,
        )