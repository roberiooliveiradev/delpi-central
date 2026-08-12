from __future__ import annotations

import json
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class InstanciaDecomposicaoEscopoRepository(PluginBaseRepository):
    def get(self, instancia_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT
                instancia_id, node_ids, inherit_all, include_descendants,
                created_at, updated_at
            FROM transformometro.instancia_decomposicao_escopo
            WHERE instancia_id = %s::uuid
            """,
            (instancia_id,),
        )

    def upsert(
        self,
        instancia_id: str,
        *,
        node_ids: list[str],
        inherit_all: bool,
        include_descendants: bool,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.instancia_decomposicao_escopo (
                instancia_id, node_ids, inherit_all, include_descendants, updated_at
            ) VALUES (%s::uuid, %s::jsonb, %s, %s, NOW())
            ON CONFLICT (instancia_id) DO UPDATE SET
                node_ids = EXCLUDED.node_ids,
                inherit_all = EXCLUDED.inherit_all,
                include_descendants = EXCLUDED.include_descendants,
                updated_at = NOW()
            RETURNING
                instancia_id, node_ids, inherit_all, include_descendants,
                created_at, updated_at
            """,
            (instancia_id, json.dumps(node_ids), inherit_all, include_descendants),
        )
        return row or {}

    def list_all(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                instancia_id, node_ids, inherit_all, include_descendants,
                created_at, updated_at
            FROM transformometro.instancia_decomposicao_escopo
            ORDER BY instancia_id ASC
            """
        )

    def upsert_from_backup(self, row: dict[str, Any], *, auto_commit: bool = False) -> None:
        self.execute(
            """
            INSERT INTO transformometro.instancia_decomposicao_escopo (
                instancia_id, node_ids, inherit_all, include_descendants,
                created_at, updated_at
            ) VALUES (%s::uuid, %s::jsonb, %s, %s, %s, %s)
            ON CONFLICT (instancia_id) DO UPDATE SET
                node_ids = EXCLUDED.node_ids,
                inherit_all = EXCLUDED.inherit_all,
                include_descendants = EXCLUDED.include_descendants,
                updated_at = EXCLUDED.updated_at
            """,
            (
                row["instancia_id"],
                json.dumps(row.get("node_ids") or []),
                bool(row.get("inherit_all", True)),
                bool(row.get("include_descendants", True)),
                row.get("created_at"),
                row.get("updated_at"),
            ),
            auto_commit=auto_commit,
        )
