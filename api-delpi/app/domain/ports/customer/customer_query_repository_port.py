from abc import ABC, abstractmethod

from app.application.models.page import Page
from app.domain.entities.customer.customer_master import CustomerMaster


class CustomerQueryRepositoryPort(ABC):
    @abstractmethod
    def search_customers(
        self,
        *,
        code: str | None = None,
        name: str | None = None,
        store: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Page[CustomerMaster]:
        raise NotImplementedError
