from __future__ import annotations

from typing import Protocol

from production_control_app.domain.product_3d_model import Product3DModel


class Product3DModelRepositoryPort(Protocol):
    def get(self, *, product_code: str) -> Product3DModel | None:
        ...

    def list(self, *, search: str | None = None) -> list[Product3DModel]:
        ...

    def existing_codes(self, codes: set[str]) -> set[str]:
        ...

    def upsert(self, model: Product3DModel) -> Product3DModel:
        ...

    def delete(self, *, product_code: str) -> Product3DModel | None:
        ...
