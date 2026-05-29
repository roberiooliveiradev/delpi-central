from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.domain.ports.commercial.commercial_proposals_repository_port import (
    CommercialProposalsRepositoryPort,
)


class ListCommercialProposalsUseCase:
    def __init__(
        self,
        commercial_proposals_repository: CommercialProposalsRepositoryPort,
    ):
        self._commercial_proposals_repository = commercial_proposals_repository

    def execute(self, request: ListCommercialProposalsRequest) -> dict:
        page = self._commercial_proposals_repository.list_proposals(request)
        return page.to_dict()
