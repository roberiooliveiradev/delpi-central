from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from app.application.dto.inspecoes_entrada.inspecoes_entrada_historico_filters import (
        InspecoesEntradaHistoricoFilters,
    )


class InspecoesEntradaRepositoryPort(Protocol):
    def get_resumo_by_branch(self, branch: str) -> dict | None: ...

    def count_pendentes_by_branch(self, branch: str) -> int: ...

    def list_pendentes_by_branch(
        self,
        branch: str,
        *,
        page: int,
        page_size: int,
    ) -> list[dict]: ...

    def list_pendentes_fornecedor_by_branch(self, branch: str) -> list[dict]: ...

    def list_rejeitadas_ensaiador_by_branch(self, branch: str) -> list[dict]: ...

    def count_rejeitadas_by_branch(self, branch: str) -> int: ...

    def list_rejeitadas_by_branch(self, branch: str, *, limit: int) -> list[dict]: ...

    def count_historico_by_branch(
        self,
        branch: str,
        filters: InspecoesEntradaHistoricoFilters,
    ) -> int: ...

    def list_historico_by_branch(
        self,
        branch: str,
        *,
        page: int,
        page_size: int,
        filters: InspecoesEntradaHistoricoFilters,
    ) -> list[dict]: ...

    def get_historico_header_by_inspection_id(
        self,
        branch: str,
        inspection_id: str,
    ) -> dict | None: ...

    def list_tests_by_inspection_header(
        self,
        branch: str,
        header: dict,
    ) -> list[dict]: ...
