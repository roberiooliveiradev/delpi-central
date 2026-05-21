from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class RevisaoRepository(PluginBaseRepository):
    def list_by_processo(self, processo_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM transformometro.revisoes
            WHERE processo_id = %s AND deletado = FALSE
            ORDER BY data_inicio_vigencia DESC, versao_revisao DESC
            """,
            (processo_id,),
        )

    def get(self, revisao_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT * FROM transformometro.revisoes
            WHERE revisao_id = %s AND deletado = FALSE
            """,
            (revisao_id,),
        )

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        chave = f"{data['processo_id']}|{data['versao_revisao']}"
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.revisoes (
                processo_id, versao_revisao, chave_unica_processo_revisao,
                descricao_revisao, motivo_revisao, cenario_tipo,
                data_implantacao, data_inicio_vigencia, data_fim_vigencia,
                revisao_ativa, observacoes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["processo_id"],
                data["versao_revisao"],
                chave,
                data.get("descricao_revisao"),
                data.get("motivo_revisao"),
                data["cenario_tipo"],
                data.get("data_implantacao"),
                data["data_inicio_vigencia"],
                data.get("data_fim_vigencia"),
                data.get("revisao_ativa", False),
                data.get("observacoes"),
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao criar revisão.")
        return row

    def update(self, revisao_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        chave = f"{data['processo_id']}|{data['versao_revisao']}"
        return self.execute_returning_one(
            """
            UPDATE transformometro.revisoes SET
                processo_id = %s,
                versao_revisao = %s,
                chave_unica_processo_revisao = %s,
                descricao_revisao = %s,
                motivo_revisao = %s,
                cenario_tipo = %s,
                data_implantacao = %s,
                data_inicio_vigencia = %s,
                data_fim_vigencia = %s,
                revisao_ativa = %s,
                observacoes = %s,
                updated_at = NOW()
            WHERE revisao_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (
                data["processo_id"],
                data["versao_revisao"],
                chave,
                data.get("descricao_revisao"),
                data.get("motivo_revisao"),
                data["cenario_tipo"],
                data.get("data_implantacao"),
                data["data_inicio_vigencia"],
                data.get("data_fim_vigencia"),
                data.get("revisao_ativa", False),
                data.get("observacoes"),
                revisao_id,
            ),
        )

    def activate(self, revisao_id: str) -> dict[str, Any] | None:
        current = self.get(revisao_id)
        if not current:
            return None

        self.execute(
            """
            UPDATE transformometro.revisoes
            SET revisao_ativa = FALSE, updated_at = NOW()
            WHERE processo_id = %s AND deletado = FALSE
            """,
            (str(current["processo_id"]),),
            auto_commit=False,
        )
        return self.execute_returning_one(
            """
            UPDATE transformometro.revisoes
            SET revisao_ativa = TRUE, updated_at = NOW()
            WHERE revisao_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (revisao_id,),
        )

    def soft_delete(self, revisao_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.revisoes
            SET deletado = TRUE, revisao_ativa = FALSE, updated_at = NOW()
            WHERE revisao_id = %s AND deletado = FALSE
            RETURNING revisao_id
            """,
            (revisao_id,),
        )
        return row is not None
