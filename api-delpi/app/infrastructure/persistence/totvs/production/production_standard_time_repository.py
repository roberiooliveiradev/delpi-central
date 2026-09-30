"""Repository — contexto de tempo padrão de uma operação de OP."""

from __future__ import annotations

from typing import Any

from app.domain.ports.production.production_standard_time_repository_port import (
    ProductionStandardTimeRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.production.production_standard_time_sql import (
    build_operation_standard_time_query,
)


class ProductionStandardTimeRepository(
    BaseRepository, ProductionStandardTimeRepositoryPort
):
    def get_operation_standard_time_context(
        self,
        *,
        branch: str,
        production_order: str,
        operation_code: str,
    ) -> dict[str, Any] | None:
        query = build_operation_standard_time_query()
        params = (
            branch,
            production_order,
            operation_code,
            branch,
            operation_code,
            branch,
            production_order,
        )
        # Sem cache: o snapshot SHY/SG2 é chaveado por OP+operação e muda com o
        # cadastro TOTVS — nunca devolver o padrão de outra OP.
        with self:
            rows = self.execute_query(query, params) or []
        return rows[0] if rows else None
