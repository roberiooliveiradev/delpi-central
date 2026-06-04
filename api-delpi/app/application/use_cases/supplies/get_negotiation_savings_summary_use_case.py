from app.application.dto.supplies.negotiation_savings_summary_request import (
    NegotiationSavingsSummaryRequest,
)
from app.application.dto.supplies.negotiation_savings_summary_response import (
    NegotiationSavingsSummaryResponse,
)
from app.domain.ports.supplies.negotiation_savings_query_repository_port import (
    NegotiationSavingsQueryRepositoryPort,
)


class GetNegotiationSavingsSummaryUseCase:
    def __init__(self, repository: NegotiationSavingsQueryRepositoryPort) -> None:
        self._repository = repository

    def execute(
        self,
        request: NegotiationSavingsSummaryRequest,
    ) -> NegotiationSavingsSummaryResponse:
        return self._repository.get_summary(request)
