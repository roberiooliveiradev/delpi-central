from app.application.dto.customer.search_customers_request import SearchCustomersRequest
from app.application.models.page import Page
from app.domain.entities.customer.customer_master import CustomerMaster
from app.domain.ports.customer.customer_query_repository_port import CustomerQueryRepositoryPort


class SearchCustomersUseCase:
    def __init__(self, repository: CustomerQueryRepositoryPort):
        self._repository = repository

    def execute(self, request: SearchCustomersRequest) -> Page[CustomerMaster]:
        return self._repository.search_customers(
            code=request.code,
            name=request.name,
            store=request.store,
            page=request.page,
            page_size=request.page_size,
        )
