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
        sort_by: str | None = None,
        sort_dir: str | None = None,
        incluir_bloqueados: bool | None = None,
    ) -> dict: ...

    def obter_ferramenta(self, codigo: str) -> dict: ...

    def listar_pecas(self, codigo_ferramenta: str) -> dict: ...

    def obter_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        data_inicial: str,
        data_final: str,
    ) -> dict: ...

    def listar_componentes(self, *, codigo_ferramenta: str, filial: str) -> dict: ...

    def listar_onde_usado(self, *, codigo_ferramenta: str) -> dict: ...
