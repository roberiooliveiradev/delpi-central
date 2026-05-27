from __future__ import annotations

from datetime import date, timedelta
from typing import Any

from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)
from tm_app.infrastructure.persistence.repositories.recurso_repository import RecursoRepository


class RecursoCustoRepository(PluginBaseRepository):
    def list_by_recurso(self, recurso_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM transformometro.recurso_custos
            WHERE recurso_compartilhado_id = %s AND deletado = FALSE
            ORDER BY data_inicio_vigencia DESC, created_at DESC
            """,
            (recurso_id,),
        )

    def list_all(self) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT * FROM transformometro.recurso_custos
            WHERE deletado = FALSE
            ORDER BY recurso_compartilhado_id, data_inicio_vigencia ASC
            """
        )

    def get(self, recurso_custo_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT * FROM transformometro.recurso_custos
            WHERE recurso_custo_id = %s AND deletado = FALSE
            """,
            (recurso_custo_id,),
        )

    def create(self, data: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.recurso_custos (
                recurso_compartilhado_id, valor_mensal,
                data_inicio_vigencia, data_fim_vigencia, observacoes
            ) VALUES (%s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["recurso_compartilhado_id"],
                data["valor_mensal"],
                data["data_inicio_vigencia"],
                data.get("data_fim_vigencia"),
                data.get("observacoes"),
            ),
        )
        if row is None:
            raise RuntimeError("Falha ao criar vigência de custo.")
        self.sync_valor_atual(str(data["recurso_compartilhado_id"]))
        return row

    def update(self, recurso_custo_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.recurso_custos SET
                valor_mensal = %s,
                data_inicio_vigencia = %s,
                data_fim_vigencia = %s,
                observacoes = %s,
                updated_at = NOW()
            WHERE recurso_custo_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (
                data["valor_mensal"],
                data["data_inicio_vigencia"],
                data.get("data_fim_vigencia"),
                data.get("observacoes"),
                recurso_custo_id,
            ),
        )
        if row:
            self.sync_valor_atual(str(row["recurso_compartilhado_id"]))
        return row

    def soft_delete(self, recurso_custo_id: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE transformometro.recurso_custos
            SET deletado = TRUE, updated_at = NOW()
            WHERE recurso_custo_id = %s AND deletado = FALSE
            RETURNING recurso_compartilhado_id
            """,
            (recurso_custo_id,),
        )
        if row:
            self.sync_valor_atual(str(row["recurso_compartilhado_id"]))
            return True
        return False

    def create_initial(
        self,
        recurso_id: str,
        valor_mensal: float,
        data_inicio_vigencia: str | None,
    ) -> dict[str, Any]:
        inicio = data_inicio_vigencia or "2000-01-01"
        return self.create(
            {
                "recurso_compartilhado_id": recurso_id,
                "valor_mensal": valor_mensal,
                "data_inicio_vigencia": inicio,
            }
        )

    def registrar_reajuste(
        self,
        recurso_id: str,
        valor_mensal: float,
        vigente_desde: str,
        observacoes: str | None = None,
    ) -> dict[str, Any]:
        inicio = date.fromisoformat(vigente_desde[:10])
        fim_anterior = inicio - timedelta(days=1)

        open_rows = self.fetch_all(
            """
            SELECT recurso_custo_id, data_inicio_vigencia
            FROM transformometro.recurso_custos
            WHERE recurso_compartilhado_id = %s
              AND deletado = FALSE
              AND data_fim_vigencia IS NULL
              AND data_inicio_vigencia < %s
            ORDER BY data_inicio_vigencia ASC
            """,
            (recurso_id, inicio),
        )
        for prev in open_rows:
            self.execute_returning_one(
                """
                UPDATE transformometro.recurso_custos SET
                    data_fim_vigencia = %s,
                    updated_at = NOW()
                WHERE recurso_custo_id = %s AND deletado = FALSE
                RETURNING recurso_custo_id
                """,
                (fim_anterior.isoformat(), str(prev["recurso_custo_id"])),
            )

        row = self.create(
            {
                "recurso_compartilhado_id": recurso_id,
                "valor_mensal": valor_mensal,
                "data_inicio_vigencia": inicio.isoformat(),
                "observacoes": observacoes,
            }
        )
        return row

    def sync_valor_atual(self, recurso_id: str) -> None:
        """Atualiza valor_total_recorrente no catálogo com o período vigente em aberto (ou o mais recente)."""
        row = self.fetch_one(
            """
            SELECT valor_mensal
            FROM transformometro.recurso_custos
            WHERE recurso_compartilhado_id = %s AND deletado = FALSE
            ORDER BY
                (data_fim_vigencia IS NULL) DESC,
                data_inicio_vigencia DESC
            LIMIT 1
            """,
            (recurso_id,),
        )
        if not row:
            return
        recurso = RecursoRepository(connection=self._connection).get(recurso_id)
        if not recurso:
            return
        RecursoRepository(connection=self._connection).update(
            recurso_id,
            {
                **recurso,
                "valor_total_recorrente": float(row["valor_mensal"]),
            },
        )
