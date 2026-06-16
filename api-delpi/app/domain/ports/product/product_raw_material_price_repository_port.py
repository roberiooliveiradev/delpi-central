from abc import ABC, abstractmethod


class ProductRawMaterialPriceRepositoryPort(ABC):

    @abstractmethod
    def fetch_product_header(self, code: str) -> dict | None:
        ...

    @abstractmethod
    def fetch_last_purchase(
        self,
        code: str,
        branch: str | None = None,
    ) -> dict | None:
        ...

    @abstractmethod
    def fetch_last_purchases_for_codes(
        self,
        codes: list[str],
        branch: str | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_purchase_price_history(
        self,
        code: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
        limit: int = 24,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_purchase_budget_history(
        self,
        code: str,
        date_start: str,
        date_end_exclusive: str,
        branch: str | None = None,
    ) -> list[dict]:
        ...
