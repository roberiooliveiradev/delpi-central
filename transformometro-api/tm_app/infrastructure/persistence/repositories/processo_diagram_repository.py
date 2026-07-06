from __future__ import annotations

import json
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class ProcessoDiagramRepository(PluginBaseRepository):
    def get(self, processo_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT
                processo_id,
                conteudo,
                mermaid_cached,
                created_at,
                updated_at
            FROM transformometro.processo_diagramas
            WHERE processo_id = %s::uuid
            """,
            (processo_id,),
        )

    def upsert(
        self,
        processo_id: str,
        *,
        conteudo: dict[str, Any],
        mermaid_cached: str | None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.processo_diagramas (
                processo_id, conteudo, mermaid_cached, updated_at
            ) VALUES (%s::uuid, %s::jsonb, %s, NOW())
            ON CONFLICT (processo_id) DO UPDATE SET
                conteudo = EXCLUDED.conteudo,
                mermaid_cached = EXCLUDED.mermaid_cached,
                updated_at = NOW()
            RETURNING processo_id, conteudo, mermaid_cached, created_at, updated_at
            """,
            (processo_id, json.dumps(conteudo), mermaid_cached),
        )
        return row or {}

    def list_all(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT processo_id, conteudo, mermaid_cached, created_at, updated_at
            FROM transformometro.processo_diagramas
            ORDER BY processo_id ASC
            """
        )

    def upsert_from_backup(self, row: dict[str, Any], *, auto_commit: bool = False) -> None:
        self.execute(
            """
            INSERT INTO transformometro.processo_diagramas (
                processo_id, conteudo, mermaid_cached, created_at, updated_at
            ) VALUES (%s::uuid, %s::jsonb, %s, %s, %s)
            ON CONFLICT (processo_id) DO UPDATE SET
                conteudo = EXCLUDED.conteudo,
                mermaid_cached = EXCLUDED.mermaid_cached,
                updated_at = EXCLUDED.updated_at
            """,
            (
                row["processo_id"],
                json.dumps(row.get("conteudo") or {}),
                row.get("mermaid_cached"),
                row.get("created_at"),
                row.get("updated_at"),
            ),
            auto_commit=auto_commit,
        )
