from __future__ import annotations

from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class InvestimentoRepository(PluginBaseRepository):
    def list_by_revisao(self, revisao_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM transformometro.investimentos
            WHERE revisao_id = %s AND deletado = FALSE
            ORDER BY data_investimento DESC NULLS LAST, created_at DESC
            """,
            (revisao_id,),
        )

    def get(self, investimento_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT * FROM transformometro.investimentos
            WHERE investimento_id = %s AND deletado = FALSE
            """,
            (investimento_id,),
        )

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        qty = float(data.get("quantidade") or 1)
        unit = float(data.get("valor_unitario") or 0)
        total = round(qty * unit, 2)
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.investimentos (
                revisao_id, tipo_investimento, categoria_investimento,
                descricao_item, quantidade, valor_unitario, valor_total,
                data_investimento, recorrencia, meses_vigencia, centro_custo, observacoes
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["revisao_id"],
                data["tipo_investimento"],
                data.get("categoria_investimento"),
                data["descricao_item"],
                qty,
                unit,
                total,
                data.get("data_investimento"),
                data.get("recorrencia", "unico"),
                data.get("meses_vigencia"),
                data.get("centro_custo"),
                data.get("observacoes"),
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao criar investimento.")
        return row

    def update(self, investimento_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        qty = float(data.get("quantidade") or 1)
        unit = float(data.get("valor_unitario") or 0)
        total = round(qty * unit, 2)
        return self.execute_returning_one(
            """
            UPDATE transformometro.investimentos SET
                tipo_investimento = %s,
                categoria_investimento = %s,
                descricao_item = %s,
                quantidade = %s,
                valor_unitario = %s,
                valor_total = %s,
                data_investimento = %s,
                recorrencia = %s,
                meses_vigencia = %s,
                centro_custo = %s,
                observacoes = %s,
                updated_at = NOW()
            WHERE investimento_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (
                data["tipo_investimento"],
                data.get("categoria_investimento"),
                data["descricao_item"],
                qty,
                unit,
                total,
                data.get("data_investimento"),
                data.get("recorrencia", "unico"),
                data.get("meses_vigencia"),
                data.get("centro_custo"),
                data.get("observacoes"),
                investimento_id,
            ),
        )

    def soft_delete(self, investimento_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.investimentos
            SET deletado = TRUE, updated_at = NOW()
            WHERE investimento_id = %s AND deletado = FALSE
            RETURNING investimento_id
            """,
            (investimento_id,),
        )
        return row is not None
