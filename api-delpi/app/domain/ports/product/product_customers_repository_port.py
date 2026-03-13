# app/domain/ports/product_customers_repository_port.py
from abc import ABC, abstractmethod
from app.application.models.page import Page
from app.domain.entities.product.customer import Customer


class ProductCustomersRepositoryPort(ABC):

    @abstractmethod
    def list_customers(
        self,
        code: str,
        page: int,
        page_size: int
    ) -> Page[Customer]:
        pass