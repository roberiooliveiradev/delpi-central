from abc import ABC, abstractmethod


class ProductExclusiveRawMaterialRepositoryPort(ABC):

    @abstractmethod
    def fetch_exclusive_catalog_by_material(
        self,
        *,
        max_depth: int,
        limit: int,
        offset: int,
        include_test_products: bool,
        finished_product_code: str | None = None,
        raw_material_code: str | None = None,
        group_code: str | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_exclusive_catalog_by_finished_product(
        self,
        *,
        max_depth: int,
        limit: int,
        offset: int,
        include_test_products: bool,
        finished_product_code: str | None = None,
        raw_material_code: str | None = None,
        group_code: str | None = None,
    ) -> list[dict]:
        ...

    @abstractmethod
    def fetch_exclusive_catalog_totals(
        self,
        *,
        max_depth: int,
        include_test_products: bool,
        finished_product_code: str | None = None,
        raw_material_code: str | None = None,
        group_code: str | None = None,
    ) -> dict:
        ...
