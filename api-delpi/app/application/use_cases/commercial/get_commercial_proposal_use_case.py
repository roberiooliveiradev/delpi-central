from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)
from app.domain.ports.commercial.commercial_proposals_repository_port import (
    CommercialProposalsRepositoryPort,
)


class GetCommercialProposalUseCase:
    def __init__(
        self,
        commercial_proposals_repository: CommercialProposalsRepositoryPort,
    ):
        self._commercial_proposals_repository = commercial_proposals_repository

    def execute(self, request: GetCommercialProposalRequest) -> dict:
        proposal = self._commercial_proposals_repository.get_proposal(request)
        if proposal is None:
            raise ValueError("Proposta comercial não encontrada.")
        return proposal.to_dict()
