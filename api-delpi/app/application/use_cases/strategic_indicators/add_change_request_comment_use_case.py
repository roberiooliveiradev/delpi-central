from app.application.dto.strategic_indicators.add_change_request_comment_request import (
    AddStrategicIndicatorsChangeRequestCommentRequest,
)
from app.domain.ports.strategic_indicators.change_request_repository_port import (
    StrategicIndicatorsChangeRequestRepositoryPort,
)


class AddStrategicIndicatorsChangeRequestCommentUseCase:
    def __init__(self, repository: StrategicIndicatorsChangeRequestRepositoryPort):
        self._repository = repository

    def execute(
        self,
        request: AddStrategicIndicatorsChangeRequestCommentRequest,
    ) -> dict:
        if not request.comment_text.strip():
            raise ValueError("comment_text é obrigatório.")

        return self._repository.add_comment(
            change_request_id=request.change_request_id,
            comment_text=request.comment_text.strip(),
            actor_user_id=request.actor_user_id,
            actor_email=request.actor_email,
        )