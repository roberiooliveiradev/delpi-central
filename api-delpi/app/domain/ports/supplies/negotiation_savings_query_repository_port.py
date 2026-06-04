from abc import ABC, abstractmethod

from app.application.dto.supplies.negotiation_savings_summary_request import (
    NegotiationSavingsSummaryRequest,
)
from app.application.dto.supplies.negotiation_savings_summary_response import (
    NegotiationSavingsSummaryResponse,
)


class NegotiationSavingsQueryRepositoryPort(ABC):
    @abstractmethod
    def get_summary(
        self,
        request: NegotiationSavingsSummaryRequest,
    ) -> NegotiationSavingsSummaryResponse:
        raise NotImplementedError
