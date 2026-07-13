from __future__ import annotations

from typing import Protocol


class InspecoesProcessoRepositoryPort(Protocol):
    def get_resumo_by_branch(self, branch: str) -> dict | None: ...

    def list_ranking_ensaio_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]: ...

    def list_por_produto_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]: ...

    def list_por_operacao_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]: ...

    def list_por_ensaiador_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]: ...

    def list_historico_by_branch(
        self,
        branch: str,
        *,
        offset: int,
        fetch_next: int,
        ordem_producao: str | None = None,
        codigo_produto: str | None = None,
        resultado: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> list[dict]: ...

    def get_historico_cabecalho_by_op(
        self,
        branch: str,
        *,
        ordem_producao: str,
    ) -> dict | None: ...

    def list_historico_detalhe_itens_by_op(
        self,
        branch: str,
        *,
        ordem_producao: str,
        offset: int,
        fetch_next: int,
    ) -> list[dict]: ...

    def list_auditoria_apontamentos_page(
        self,
        branch: str,
        *,
        data: str,
        offset: int,
        fetch_next: int,
    ) -> tuple[dict, list[dict]]: ...
