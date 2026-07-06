from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_EVIDENCE_SELECT = """
    SELECT
        e.evidencia_id,
        e.revisao_id,
        e.tipo,
        e.nome_arquivo,
        e.nome_armazenado,
        e.tipo_mime,
        e.tamanho_bytes,
        e.descricao,
        e.url_externa,
        e.enviado_por_id,
        e.enviado_por_nome,
        e.created_at
    FROM transformometro.revisao_evidencias e
"""

_VALID_TYPES = {"anexo", "foto", "documento", "link"}


class RevisaoEvidenceRepository(PluginBaseRepository):
    def list_by_revisao(self, revisao_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            {_EVIDENCE_SELECT}
            WHERE e.revisao_id = %s::uuid
              AND e.deleted_at IS NULL
            ORDER BY e.created_at DESC
            """,
            (revisao_id,),
        )

    def get(self, revisao_id: str, evidencia_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            {_EVIDENCE_SELECT}
            WHERE e.revisao_id = %s::uuid
              AND e.evidencia_id = %s::uuid
              AND e.deleted_at IS NULL
            """,
            (revisao_id, evidencia_id),
        )

    def create(
        self,
        revisao_id: str,
        fields: dict[str, Any],
        *,
        auto_commit: bool = True,
    ) -> dict[str, Any]:
        evidence_type = fields.get("tipo", "anexo")
        if evidence_type not in _VALID_TYPES:
            evidence_type = "anexo"

        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.revisao_evidencias (
                revisao_id, tipo, nome_arquivo, nome_armazenado, tipo_mime, tamanho_bytes,
                descricao, url_externa, enviado_por_id, enviado_por_nome
            ) VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING evidencia_id
            """,
            (
                revisao_id,
                evidence_type,
                fields.get("nome_arquivo"),
                fields.get("nome_armazenado"),
                fields.get("tipo_mime"),
                fields.get("tamanho_bytes"),
                fields.get("descricao"),
                fields.get("url_externa"),
                fields.get("enviado_por_id"),
                fields.get("enviado_por_nome"),
            ),
            auto_commit=auto_commit,
        )
        created = self.get(revisao_id, str(row["evidencia_id"])) if row else None
        return created or {}

    def update(
        self,
        revisao_id: str,
        evidencia_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any] | None:
        sets: list[str] = []
        params: list[Any] = []
        if "descricao" in fields:
            sets.append("descricao = %s")
            params.append(fields["descricao"])
        if not sets:
            return self.get(revisao_id, evidencia_id)

        params.extend([revisao_id, evidencia_id])
        row = self.execute_returning_one(
            f"""
            UPDATE transformometro.revisao_evidencias
               SET {", ".join(sets)}
             WHERE revisao_id = %s::uuid
               AND evidencia_id = %s::uuid
               AND deleted_at IS NULL
            RETURNING evidencia_id
            """,
            tuple(params),
        )
        if not row:
            return None
        return self.get(revisao_id, evidencia_id)

    def soft_delete(self, revisao_id: str, evidencia_id: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE transformometro.revisao_evidencias
               SET deleted_at = NOW()
             WHERE revisao_id = %s::uuid
               AND evidencia_id = %s::uuid
               AND deleted_at IS NULL
            RETURNING evidencia_id, nome_armazenado
            """,
            (revisao_id, evidencia_id),
        )
