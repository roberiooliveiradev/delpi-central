from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ListOpsAbertasResponse:
    items: list[dict]
    resumo: list[dict]

    def to_dict(self) -> dict:
        return {
            "items": self.items,
            "resumo": self.resumo,
        }
