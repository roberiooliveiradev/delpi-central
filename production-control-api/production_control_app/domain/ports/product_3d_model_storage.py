from __future__ import annotations

from typing import Protocol


class Product3DModelStoragePort(Protocol):
    def write_glb(self, *, product_code: str, payload: bytes) -> str:
        ...

    def resolve_glb(self, *, stored_filename: str) -> str:
        ...

    def delete_glb(self, *, stored_filename: str) -> None:
        ...
