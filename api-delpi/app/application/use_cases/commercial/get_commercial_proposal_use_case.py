from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)
from app.domain.ports.commercial.commercial_proposals_repository_port import (
    CommercialProposalsRepositoryPort,
)
from app.domain.ports.lmp.lmp_query_repository_port import LMPQueryRepositoryPort


class GetCommercialProposalUseCase:
    def __init__(
        self,
        commercial_proposals_repository: CommercialProposalsRepositoryPort,
        lmp_query_repository: LMPQueryRepositoryPort,
    ):
        self._commercial_proposals_repository = commercial_proposals_repository
        self._lmp_query_repository = lmp_query_repository

    def execute(self, request: GetCommercialProposalRequest) -> dict:
        proposal = self._commercial_proposals_repository.get_proposal(request)
        if proposal is None:
            raise ValueError("Proposta comercial não encontrada.")

        products = self._lmp_query_repository.list_ov_products(
            sale_number=request.proposal_number,
            requested_branch=request.branch,
        )

        payload = proposal.to_dict()
        payload["list_products"] = [product.to_dict() for product in products]
        return payload
