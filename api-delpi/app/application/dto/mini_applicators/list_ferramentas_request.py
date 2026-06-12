from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListMiniApplicatorsFerramentasRequest:
    codigo: str | None = None
    descricao: str | None = None
    filial: str | None = None
    page: int = 1
    page_size: int = 50
