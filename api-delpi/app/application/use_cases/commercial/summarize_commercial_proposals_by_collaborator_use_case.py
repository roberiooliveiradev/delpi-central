from app.application.dto.commercial.summarize_commercial_proposals_by_collaborator_request import (
    SummarizeCommercialProposalsByCollaboratorRequest,
)
from app.domain.ports.commercial.commercial_proposals_repository_port import (
    CommercialProposalsRepositoryPort,
)


class SummarizeCommercialProposalsByCollaboratorUseCase:
    def __init__(
        self,
        commercial_proposals_repository: CommercialProposalsRepositoryPort,
    ):
        self._commercial_proposals_repository = commercial_proposals_repository

    def execute(
        self, request: SummarizeCommercialProposalsByCollaboratorRequest
    ) -> dict:
        return self._commercial_proposals_repository.summarize_by_collaborator(request)
