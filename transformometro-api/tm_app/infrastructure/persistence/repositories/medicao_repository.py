from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class MedicaoRepository(PluginBaseRepository):
    def get_by_revisao(self, revisao_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT * FROM transformometro.medicoes
            WHERE revisao_id = %s AND deletado = FALSE
            """,
            (revisao_id,),
        )

    def create(self, data: dict[str, Any], *, auto_commit: bool = True) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.medicoes (
                revisao_id, volume_mensal, tempo_medio_execucao_min,
                tempo_retrabalho_min, percentual_retrabalho, percentual_erro,
                quantidade_erros_mes, custo_hora_mao_obra, custo_unitario_erro,
                custo_unitario_retrabalho, custo_outros_desperdicios,
                base_referencia_mes, observacoes
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING *
            """,
            (
                data["revisao_id"],
                data.get("volume_mensal", 0),
                data.get("tempo_medio_execucao_min", 0),
                data.get("tempo_retrabalho_min", 0),
                data.get("percentual_retrabalho", 0),
                data.get("percentual_erro", 0),
                data.get("quantidade_erros_mes", 0),
                data.get("custo_hora_mao_obra", 0),
                data.get("custo_unitario_erro", 0),
                data.get("custo_unitario_retrabalho", 0),
                data.get("custo_outros_desperdicios", 0),
                data.get("base_referencia_mes"),
                data.get("observacoes"),
            ),
            auto_commit=auto_commit,
        )
        if row is None:
            raise RuntimeError("Falha ao criar medição.")
        return row

    def upsert(self, data: dict[str, Any]) -> dict[str, Any]:
        existing = self.get_by_revisao(data["revisao_id"])
        if existing:
            return self.update(str(existing["medicao_id"]), data)  # type: ignore[return-value]

        return self.create(data)

    def update(self, medicao_id: str, data: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.medicoes SET
                volume_mensal = %s,
                tempo_medio_execucao_min = %s,
                tempo_retrabalho_min = %s,
                percentual_retrabalho = %s,
                percentual_erro = %s,
                quantidade_erros_mes = %s,
                custo_hora_mao_obra = %s,
                custo_unitario_erro = %s,
                custo_unitario_retrabalho = %s,
                custo_outros_desperdicios = %s,
                base_referencia_mes = %s,
                observacoes = %s,
                updated_at = NOW()
            WHERE medicao_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (
                data.get("volume_mensal", 0),
                data.get("tempo_medio_execucao_min", 0),
                data.get("tempo_retrabalho_min", 0),
                data.get("percentual_retrabalho", 0),
                data.get("percentual_erro", 0),
                data.get("quantidade_erros_mes", 0),
                data.get("custo_hora_mao_obra", 0),
                data.get("custo_unitario_erro", 0),
                data.get("custo_unitario_retrabalho", 0),
                data.get("custo_outros_desperdicios", 0),
                data.get("base_referencia_mes"),
                data.get("observacoes"),
                medicao_id,
            ),
        )
        if row is None:
            raise RuntimeError("Medição não encontrada.")
        return row

    def soft_delete(self, medicao_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.medicoes
            SET deletado = TRUE, updated_at = NOW()
            WHERE medicao_id = %s AND deletado = FALSE
            RETURNING medicao_id
            """,
            (medicao_id,),
        )
        return row is not None
