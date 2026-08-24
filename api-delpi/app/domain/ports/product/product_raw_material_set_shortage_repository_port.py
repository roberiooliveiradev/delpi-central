from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class ProductRawMaterialSetShortageRepositoryPort(ABC):
    @abstractmethod
    def fetch_product(self, code: str) -> dict[str, Any] | None:
        raise NotImplementedError

    @abstractmethod
    def fetch_raw_material_bom(
        self, code: str, *, max_depth: int
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_open_mother_orders(
        self, *, code: str, branch: str
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_mp_stock(
        self, *, branch: str, product_codes: list[str]
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_open_purchase_orders(
        self, *, branch: str, product_codes: list[str]
    ) -> list[dict[str, Any]]:
        raise NotImplementedError

    @abstractmethod
    def fetch_open_commitments(
        self, *, branch: str, product_codes: list[str]
    ) -> list[dict[str, Any]]:
        raise NotImplementedError
