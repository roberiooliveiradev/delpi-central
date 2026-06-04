from abc import ABC, abstractmethod

from si_app.application.dto.supplies.negotiation_savings_summary_request import (
    NegotiationSavingsSummaryRequest,
)


class NegotiationSavingsQueryRepositoryPort(ABC):
    @abstractmethod
    def get_summary(self, request: NegotiationSavingsSummaryRequest) -> dict:
        raise NotImplementedError
