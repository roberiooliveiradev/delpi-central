"""Use case — intermediários compartilhados entre PAs ativos."""

from __future__ import annotations

from app.application.dto.production.shared_structure_intermediates_request import (
    SharedStructureIntermediatesRequest,
)
from app.application.services.production.shared_structure_intermediates_response_assembler import (
    SharedStructureIntermediatesResponseAssembler,
)
from app.domain.ports.production.shared_structure_intermediates_repository_port import (
    SharedStructureIntermediatesRepositoryPort,
)


class GetSharedStructureIntermediatesUseCase:
    def __init__(
        self, repository: SharedStructureIntermediatesRepositoryPort
    ) -> None:
        self._repository = repository

    def execute(self, request: SharedStructureIntermediatesRequest) -> dict:
        filters = request.filter_kwargs()
        summary_row = self._repository.get_shared_intermediates_summary(**filters)
        rows = self._repository.get_shared_intermediates(
            **filters,
            offset=request.offset,
            page_size=request.page_size,
        )
        return SharedStructureIntermediatesResponseAssembler.to_paged_list(
            rows, summary_row=summary_row, request=request
        )
