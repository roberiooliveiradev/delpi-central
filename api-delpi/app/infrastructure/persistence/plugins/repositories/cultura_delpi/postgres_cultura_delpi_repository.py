from __future__ import annotations

import json
from datetime import datetime
from typing import Any

from app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class PostgresCulturaDelpiRepository(PluginBaseRepository):
    _SINGLETON_ID = 1

    def get_content(self) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT proposito,
                   missao,
                   visao,
                   valores,
                   updated_at,
                   updated_by_user_id,
                   updated_by_name
              FROM cultura_delpi.content
             WHERE id = %s
            """,
            (self._SINGLETON_ID,),
        )

    def update_content(
        self,
        *,
        proposito: str,
        missao: str,
        visao: str,
        valores: list[str],
        updated_by_user_id: str | None,
        updated_by_name: str | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            UPDATE cultura_delpi.content
               SET proposito = %s,
                   missao = %s,
                   visao = %s,
                   valores = %s::jsonb,
                   updated_at = NOW(),
                   updated_by_user_id = %s,
                   updated_by_name = %s
             WHERE id = %s
            RETURNING proposito,
                      missao,
                      visao,
                      valores,
                      updated_at,
                      updated_by_user_id,
                      updated_by_name
            """,
            (
                proposito,
                missao,
                visao,
                json.dumps(valores),
                updated_by_user_id,
                updated_by_name,
                self._SINGLETON_ID,
            ),
        )
        if row is None:
            raise RuntimeError("Conteúdo Cultura DELPI não encontrado (singleton id=1).")
        return row

    @staticmethod
    def row_to_payload(row: dict[str, Any]) -> dict[str, Any]:
        valores = row.get("valores")
        if isinstance(valores, str):
            valores = json.loads(valores)
        if valores is None:
            valores = []

        updated_at = row.get("updated_at")
        if isinstance(updated_at, datetime):
            updated_at = updated_at.isoformat()

        return {
            "proposito": row.get("proposito") or "",
            "missao": row.get("missao") or "",
            "visao": row.get("visao") or "",
            "valores": list(valores),
            "updatedAt": updated_at,
            "updatedByUserId": row.get("updated_by_user_id"),
            "updatedByName": row.get("updated_by_name"),
        }
