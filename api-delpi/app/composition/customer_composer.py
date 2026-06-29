from app.application.use_cases.customer.search_customers_use_case import SearchCustomersUseCase
from app.infrastructure.persistence.totvs.customer_repositories.customer_repository import CustomerRepository


def build_search_customers_use_case() -> SearchCustomersUseCase:
    return SearchCustomersUseCase(CustomerRepository())
