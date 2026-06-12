from __future__ import annotations

import json
from typing import Any

from maint_app.application.list_query import ListQuery
from maint_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository


class AuditRepository(PluginBaseRepository):
    def log(
        self,
        *,
        entidade: str,
        entidade_id: str,
        acao: str,
        filial: str | None = None,
        usuario_sub: str | None = None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO maintenance.audit_logs (
                entidade, entidade_id, acao, filial, payload, usuario_sub
            ) VALUES (%s, %s, %s, %s, %s::jsonb, %s)
            """,
            (
                entidade,
                entidade_id,
                acao,
                filial,
                json.dumps(payload or {}, default=str),
                usuario_sub,
            ),
        )

    def list_by_ferramenta_paged(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        query: ListQuery,
    ) -> tuple[list[dict[str, Any]], int]:
        select_sql = """
            SELECT
                audit_id,
                entidade,
                entidade_id,
                acao,
                filial,
                payload,
                usuario_sub,
                data_criacao
            FROM maintenance.audit_logs
            WHERE filial = %s
              AND entidade = 'ferramenta'
              AND entidade_id = %s
            ORDER BY data_criacao DESC
        """
        count_sql = """
            SELECT COUNT(1) AS total
            FROM maintenance.audit_logs
            WHERE filial = %s
              AND entidade = 'ferramenta'
              AND entidade_id = %s
        """
        params = (filial, codigo_ferramenta)
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=params,
            page=query.page,
            page_size=query.page_size,
        )
