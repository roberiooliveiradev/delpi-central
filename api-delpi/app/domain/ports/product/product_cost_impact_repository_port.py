from abc import ABC, abstractmethod


class ProductCostImpactRepositoryPort(ABC):

    @abstractmethod
    def fetch_product_cost_header(self, code: str) -> dict | None:
        ...

    @abstractmethod
    def fetch_raw_material_cost_items(self, code: str, max_depth: int) -> list[dict]:
        ...
