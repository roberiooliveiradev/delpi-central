from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ProductRawMaterialSetShortageRequest:
    code: str
    branch: str
    max_depth: int = 8
