from abc import ABC, abstractmethod

from app.application.dto.commercial.list_commercial_proposals_request import (
    ListCommercialProposalsRequest,
)
from app.application.models.page import Page
from app.domain.entities.commercial.commercial_proposal import CommercialProposal


class CommercialProposalsRepositoryPort(ABC):
    @abstractmethod
    def list_proposals(
        self,
        request: ListCommercialProposalsRequest,
    ) -> Page[CommercialProposal]:
        raise NotImplementedError
