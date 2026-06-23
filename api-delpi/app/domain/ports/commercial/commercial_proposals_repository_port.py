from abc import ABC, abstractmethod

from app.application.dto.commercial.get_commercial_proposal_request import (
    GetCommercialProposalRequest,
)
from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.application.models.page import Page
from app.domain.entities.commercial.commercial_proposal import CommercialProposal
from app.domain.entities.commercial.commercial_proposal_detail import (
    CommercialProposalDetail,
)


class CommercialProposalsRepositoryPort(ABC):
    @abstractmethod
    def list_proposals(
        self,
        request: ListCommercialProposalsRequest,
    ) -> Page[CommercialProposal]:
        raise NotImplementedError

    @abstractmethod
    def get_proposal(
        self,
        request: GetCommercialProposalRequest,
    ) -> CommercialProposalDetail | None:
        raise NotImplementedError
