from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_ARQUIVO_SELECT = """
    SELECT
        a.arquivo_id,
        a.processo_id,
        a.tipo,
        a.nome_arquivo,
        a.nome_armazenado,
        a.tipo_mime,
        a.tamanho_bytes,
        a.descricao,
        a.url_externa,
        a.enviado_por_id,
        a.enviado_por_nome,
        a.created_at
    FROM transformometro.processo_arquivos a
"""

_VALID_TYPES = {"anexo", "foto", "documento", "link"}


class ProcessoArquivoRepository(PluginBaseRepository):
    def list_by_processo(self, processo_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            f"""
            {_ARQUIVO_SELECT}
            WHERE a.processo_id = %s::uuid
              AND a.deleted_at IS NULL
            ORDER BY a.created_at DESC
            """,
            (processo_id,),
        )

    def get(self, processo_id: str, arquivo_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            {_ARQUIVO_SELECT}
            WHERE a.processo_id = %s::uuid
              AND a.arquivo_id = %s::uuid
              AND a.deleted_at IS NULL
            """,
            (processo_id, arquivo_id),
        )

    def create(
        self,
        processo_id: str,
        fields: dict[str, Any],
        *,
        auto_commit: bool = True,
    ) -> dict[str, Any]:
        arquivo_type = fields.get("tipo", "anexo")
        if arquivo_type not in _VALID_TYPES:
            arquivo_type = "anexo"

        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.processo_arquivos (
                processo_id, tipo, nome_arquivo, nome_armazenado, tipo_mime, tamanho_bytes,
                descricao, url_externa, enviado_por_id, enviado_por_nome
            ) VALUES (%s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING arquivo_id
            """,
            (
                processo_id,
                arquivo_type,
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
        created = self.get(processo_id, str(row["arquivo_id"])) if row else None
        return created or {}

    def update(
        self,
        processo_id: str,
        arquivo_id: str,
        fields: dict[str, Any],
    ) -> dict[str, Any] | None:
        sets: list[str] = []
        params: list[Any] = []
        if "descricao" in fields:
            sets.append("descricao = %s")
            params.append(fields["descricao"])
        if not sets:
            return self.get(processo_id, arquivo_id)

        params.extend([processo_id, arquivo_id])
        row = self.execute_returning_one(
            f"""
            UPDATE transformometro.processo_arquivos
               SET {", ".join(sets)}
             WHERE processo_id = %s::uuid
               AND arquivo_id = %s::uuid
               AND deleted_at IS NULL
            RETURNING arquivo_id
            """,
            tuple(params),
        )
        if not row:
            return None
        return self.get(processo_id, arquivo_id)

    def soft_delete(self, processo_id: str, arquivo_id: str) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE transformometro.processo_arquivos
               SET deleted_at = NOW()
             WHERE processo_id = %s::uuid
               AND arquivo_id = %s::uuid
               AND deleted_at IS NULL
            RETURNING arquivo_id, nome_armazenado
            """,
            (processo_id, arquivo_id),
        )
