from __future__ import annotations

from typing import Protocol


class MiniApplicatorsTotvsPort(Protocol):
    def listar_ferramentas(
        self,
        *,
        codigo: str | None = None,
        descricao: str | None = None,
        filial: str | None = None,
        page: int | None = None,
        page_size: int | None = None,
    ) -> dict: ...

    def obter_ferramenta(self, codigo: str) -> dict: ...
