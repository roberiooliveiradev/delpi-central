from __future__ import annotations

import json
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_PROCESSO_TIMELINE_WHERE = """
(
  (a.entity_type = 'processo' AND a.entity_id = %s::uuid)
  OR (
    a.entity_type = 'processo_instancia'
    AND a.entity_id IN (
      SELECT pi.instancia_id
      FROM transformometro.processo_instancias pi
      WHERE pi.processo_id = %s::uuid
    )
  )
  OR (
    a.entity_type = 'revisao'
    AND a.entity_id IN (
      SELECT r.revisao_id
      FROM transformometro.revisoes r
      JOIN transformometro.processo_instancias pi ON pi.instancia_id = r.instancia_id
      WHERE pi.processo_id = %s::uuid
    )
  )
  OR (
    a.entity_type = 'medicao'
    AND a.entity_id IN (
      SELECT m.medicao_id
      FROM transformometro.medicoes m
      JOIN transformometro.revisoes r ON r.revisao_id = m.revisao_id
      JOIN transformometro.processo_instancias pi ON pi.instancia_id = r.instancia_id
      WHERE pi.processo_id = %s::uuid
    )
  )
  OR (
    a.entity_type = 'investimento'
    AND a.entity_id IN (
      SELECT i.investimento_id
      FROM transformometro.investimentos i
      JOIN transformometro.revisoes r ON r.revisao_id = i.revisao_id
      JOIN transformometro.processo_instancias pi ON pi.instancia_id = r.instancia_id
      WHERE pi.processo_id = %s::uuid
    )
  )
  OR (
    a.entity_type = 'vinculo'
    AND a.entity_id IN (
      SELECT v.vinculo_id
      FROM transformometro.revisao_recursos_compartilhados v
      JOIN transformometro.revisoes r ON r.revisao_id = v.revisao_id
      JOIN transformometro.processo_instancias pi ON pi.instancia_id = r.instancia_id
      WHERE pi.processo_id = %s::uuid
    )
  )
)
"""


class AuditRepository(PluginBaseRepository):
    def log(
        self,
        *,
        entity_type: str,
        entity_id: str,
        action: str,
        user_id: str | None,
        user_email: str | None,
        payload: dict[str, Any] | None = None,
    ) -> None:
        self.execute(
            """
            INSERT INTO transformometro.audit_logs (
                entity_type, entity_id, action, user_id, user_email, payload_json
            ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """,
            (
                entity_type,
                entity_id,
                action,
                user_id,
                user_email,
                json.dumps(payload or {}, default=str),
            ),
        )

    def list_for_processo(
        self,
        processo_id: str,
        *,
        page: int = 1,
        page_size: int = 100,
    ) -> dict[str, Any]:
        page = max(1, page)
        page_size = min(max(1, page_size), 500)
        offset = (page - 1) * page_size
        params = (processo_id,) * 6

        count_row = self.fetch_one(
            f"""
            SELECT COUNT(*)::int AS total
            FROM transformometro.audit_logs a
            WHERE {_PROCESSO_TIMELINE_WHERE}
            """,
            params,
        )
        total = int((count_row or {}).get("total") or 0)

        rows = self.fetch_all(
            f"""
            SELECT
                a.audit_id,
                a.entity_type,
                a.entity_id,
                a.action,
                a.user_id,
                a.user_email,
                a.payload_json,
                a.created_at
            FROM transformometro.audit_logs a
            WHERE {_PROCESSO_TIMELINE_WHERE}
            ORDER BY a.created_at ASC
            LIMIT %s OFFSET %s
            """,
            (*params, page_size, offset),
        )
        return {"total": total, "items": rows, "page": page, "page_size": page_size}
