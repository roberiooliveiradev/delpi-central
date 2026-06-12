from __future__ import annotations

from datetime import date
from typing import Any

from tm_app.infrastructure.persistence.repositories.processo_instancia_repository import (
    ProcessoInstanciaRepository,
)
from tm_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)


class RevisaoRepository(PluginBaseRepository):
    def list_by_processo(self, processo_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                *,
                CASE
                    WHEN lower(coalesce(cenario_tipo, '')) = 'baseline' THEN FALSE
                    WHEN data_fim_vigencia IS NOT NULL AND data_fim_vigencia < CURRENT_DATE THEN FALSE
                    ELSE revisao_ativa
                END AS revisao_ativa
            FROM transformometro.revisoes
            WHERE processo_id = %s AND deletado = FALSE
            ORDER BY data_inicio_vigencia DESC, versao_revisao DESC
            """,
            (processo_id,),
        )

    def list_by_instancia(self, instancia_id: str) -> list[dict[str, Any]]:
        return self.fetch_all(
            """
            SELECT
                *,
                CASE
                    WHEN lower(coalesce(cenario_tipo, '')) = 'baseline' THEN FALSE
                    WHEN data_fim_vigencia IS NOT NULL AND data_fim_vigencia < CURRENT_DATE THEN FALSE
                    ELSE revisao_ativa
                END AS revisao_ativa
            FROM transformometro.revisoes
            WHERE instancia_id = %s::uuid AND deletado = FALSE
            ORDER BY data_inicio_vigencia ASC, versao_revisao ASC
            """,
            (instancia_id,),
        )

    @staticmethod
    def build_chave_unica(instancia_id: str, versao_revisao: str) -> str:
        return f"{instancia_id}|{versao_revisao}"

    def get(self, revisao_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT
                *,
                CASE
                    WHEN lower(coalesce(cenario_tipo, '')) = 'baseline' THEN FALSE
                    WHEN data_fim_vigencia IS NOT NULL AND data_fim_vigencia < CURRENT_DATE THEN FALSE
                    ELSE revisao_ativa
                END AS revisao_ativa
            FROM transformometro.revisoes
            WHERE revisao_id = %s AND deletado = FALSE
            """,
            (revisao_id,),
        )

    def create(self, data: dict[str, Any], *, auto_commit: bool = True) -> dict[str, Any]:
        data = self._normalize_lifecycle_payload(data)
        if data.get("instancia_id"):
            instancia_id = str(data["instancia_id"])
        else:
            instancia = ProcessoInstanciaRepository(connection=self._connection).ensure_from_processo(
                str(data["processo_id"])
            )
            instancia_id = str(instancia["instancia_id"])
        chave = self.build_chave_unica(instancia_id, str(data["versao_revisao"]))
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.revisoes (
                processo_id, instancia_id, versao_revisao, chave_unica_processo_revisao,
                descricao_revisao, motivo_revisao, cenario_tipo,
                data_implantacao, data_inicio_vigencia, data_fim_vigencia,
                revisao_ativa, observacoes, status_aprovacao
            ) VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                data["processo_id"],
                instancia_id,
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
                data.get("status_aprovacao", "aprovada"),
            ),
            auto_commit=False,
        )
        if row is None:
            raise RuntimeError("Falha ao criar revisão.")

        row = self._apply_revision_lifecycle(row, auto_commit=False)
        if auto_commit:
            self._connection.commit()
        return row

    def update(self, revisao_id: str, data: dict[str, Any]) -> dict[str, Any] | None:
        data = self._normalize_lifecycle_payload(data)
        current = self.get(revisao_id)
        instancia_id = str(
            data.get("instancia_id")
            or (current or {}).get("instancia_id")
            or ""
        )
        chave = self.build_chave_unica(instancia_id, str(data["versao_revisao"]))
        row = self.execute_returning_one(
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
            auto_commit=False,
        )
        if row is None:
            self._connection.commit()
            return None

        row = self._apply_revision_lifecycle(row, auto_commit=False)
        self._connection.commit()
        return row

    def set_status_aprovacao(
        self,
        revisao_id: str,
        status: str,
        *,
        aprovado_por_email: str | None = None,
        motivo_rejeicao: str | None = None,
    ) -> dict[str, Any] | None:
        aprovado_em = "NOW()" if status in ("aprovada", "rejeitada") else "NULL"
        return self.execute_returning_one(
            f"""
            UPDATE transformometro.revisoes SET
                status_aprovacao = %s,
                aprovado_em = {aprovado_em},
                aprovado_por_email = %s,
                motivo_rejeicao = %s,
                updated_at = NOW()
            WHERE revisao_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (
                status,
                aprovado_por_email,
                motivo_rejeicao if status == "rejeitada" else None,
                revisao_id,
            ),
        )

    def activate(self, revisao_id: str) -> dict[str, Any] | None:
        current = self.get(revisao_id)
        if not current:
            return None
        if self._is_baseline(current):
            return self.execute_returning_one(
                """
                UPDATE transformometro.revisoes
                SET revisao_ativa = FALSE, updated_at = NOW()
                WHERE revisao_id = %s AND deletado = FALSE
                RETURNING *
                """,
                (revisao_id,),
            )

        self.execute(
            """
            UPDATE transformometro.revisoes
            SET revisao_ativa = TRUE, data_fim_vigencia = NULL, updated_at = NOW()
            WHERE revisao_id = %s AND deletado = FALSE
            """,
            (revisao_id,),
            auto_commit=False,
        )
        current = self.get(revisao_id)
        if not current:
            self._connection.commit()
            return None
        row = self._apply_revision_lifecycle(current, auto_commit=False)
        self._connection.commit()
        return row

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

    def _normalize_lifecycle_payload(self, data: dict[str, Any]) -> dict[str, Any]:
        normalized = dict(data)
        if self._is_baseline(normalized):
            normalized["revisao_ativa"] = False
        elif normalized.get("data_fim_vigencia"):
            normalized["revisao_ativa"] = False
        return normalized

    def _apply_revision_lifecycle(
        self,
        revision: dict[str, Any],
        *,
        auto_commit: bool,
    ) -> dict[str, Any]:
        revision_id = str(revision["revisao_id"])
        processo_id = str(revision["processo_id"])

        if self._is_baseline(revision):
            self.execute(
                """
                UPDATE transformometro.revisoes
                SET revisao_ativa = FALSE, updated_at = NOW()
                WHERE revisao_id = %s AND deletado = FALSE
                """,
                (revision_id,),
                auto_commit=False,
            )
            return self.get(revision_id) or revision

        if revision.get("data_fim_vigencia"):
            self.execute(
                """
                UPDATE transformometro.revisoes
                SET revisao_ativa = FALSE, updated_at = NOW()
                WHERE revisao_id = %s AND deletado = FALSE
                """,
                (revision_id,),
                auto_commit=False,
            )
            return self.get(revision_id) or revision

        if not bool(revision.get("revisao_ativa")):
            self.execute(
                """
                UPDATE transformometro.revisoes
                SET data_fim_vigencia = COALESCE(data_fim_vigencia, CURRENT_DATE),
                    updated_at = NOW()
                WHERE revisao_id = %s AND deletado = FALSE
                """,
                (revision_id,),
                auto_commit=False,
            )
            if auto_commit:
                self._connection.commit()
            return self.get(revision_id) or revision

        boundary_date = revision.get("data_implantacao") or revision.get("data_inicio_vigencia")
        instancia_id = revision.get("instancia_id")
        if instancia_id:
            self.execute(
                """
                UPDATE transformometro.revisoes
                SET revisao_ativa = FALSE,
                    data_fim_vigencia = COALESCE(data_fim_vigencia, %s),
                    updated_at = NOW()
                WHERE instancia_id = %s::uuid
                  AND revisao_id <> %s
                  AND deletado = FALSE
                """,
                (boundary_date, str(instancia_id), revision_id),
                auto_commit=False,
            )
        else:
            self.execute(
                """
                UPDATE transformometro.revisoes
                SET revisao_ativa = FALSE,
                    data_fim_vigencia = COALESCE(data_fim_vigencia, %s),
                    updated_at = NOW()
                WHERE processo_id = %s
                  AND revisao_id <> %s
                  AND deletado = FALSE
                """,
                (boundary_date, processo_id, revision_id),
                auto_commit=False,
            )
        row = self.execute_returning_one(
            """
            UPDATE transformometro.revisoes
            SET revisao_ativa = TRUE,
                data_fim_vigencia = NULL,
                updated_at = NOW()
            WHERE revisao_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (revision_id,),
            auto_commit=False,
        )
        if auto_commit:
            self._connection.commit()
        return row or revision

    @staticmethod
    def _is_baseline(data: dict[str, Any]) -> bool:
        return str(data.get("cenario_tipo") or "").lower() == "baseline"
