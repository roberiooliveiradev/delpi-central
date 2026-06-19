from abc import ABC, abstractmethod


class ProductPlaybookRepositoryPort(ABC):

    @abstractmethod
    def fetch_product_header(self, code: str) -> dict | None:
        ...

    @abstractmethod
    def fetch_structure_with_exclusivity(
        self,
        code: str,
        max_depth: int,
        *,
        reference_date: str | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_raw_material_stock(
        self,
        code: str,
        max_depth: int,
        *,
        reference_date: str | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_production_status(
        self,
        code: str,
        reference_date: str,
        max_depth: int,
        *,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_shipping_status(
        self,
        code: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
    ) -> list[dict]:
        ...
