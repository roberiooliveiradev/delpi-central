from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ListMiniApplicatorsPecasReposicaoRequest:
    codigo: str | None = None
    descricao: str | None = None
    page: int = 1
    page_size: int = 50
    sort_by: str | None = None
    sort_dir: str = "asc"
