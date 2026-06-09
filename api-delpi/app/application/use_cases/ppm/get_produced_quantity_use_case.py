from app.application.dto.ppm.produced_quantity_request import ProducedQuantityRequest
from app.domain.ports.ppm.ppm_query_repository_port import PpmQueryRepositoryPort


class GetProducedQuantityUseCase:

    def __init__(self, repository: PpmQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: ProducedQuantityRequest):
        return self._repository.list_produced_quantity(request)
