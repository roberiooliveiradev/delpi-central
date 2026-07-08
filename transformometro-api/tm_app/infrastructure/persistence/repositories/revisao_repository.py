from __future__ import annotations

import json
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
        self._validate_referencia_payload(data, instancia_id=instancia_id)
        chave = self.build_chave_unica(instancia_id, str(data["versao_revisao"]))
        row = self.execute_returning_one(
            """
            INSERT INTO transformometro.revisoes (
                processo_id, instancia_id, versao_revisao, chave_unica_processo_revisao,
                descricao_revisao, motivo_revisao, cenario_tipo,
                data_implantacao, data_inicio_vigencia, data_fim_vigencia,
                revisao_ativa, observacoes, status_aprovacao, revisao_referencia_id
            ) VALUES (%s, %s::uuid, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::uuid)
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
                data.get("revisao_referencia_id"),
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
        self._validate_referencia_payload(
            data,
            instancia_id=instancia_id,
            revisao_id=revisao_id,
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
                revisao_referencia_id = %s::uuid,
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
                data.get("revisao_referencia_id"),
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

    def update_matriz_impacto_esforco(
        self,
        revisao_id: str,
        payload: dict[str, Any],
        *,
        auto_commit: bool = True,
    ) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE transformometro.revisoes
            SET matriz_impacto_esforco = %s::jsonb,
                updated_at = NOW()
            WHERE revisao_id = %s AND deletado = FALSE
            RETURNING *
            """,
            (json.dumps(payload), revisao_id),
            auto_commit=auto_commit,
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
            normalized["revisao_referencia_id"] = None
        elif normalized.get("data_fim_vigencia"):
            normalized["revisao_ativa"] = False
        return normalized

    def _validate_referencia_payload(
        self,
        data: dict[str, Any],
        *,
        instancia_id: str,
        revisao_id: str | None = None,
    ) -> None:
        cenario = str(data.get("cenario_tipo") or "").lower()
        referencia_id = str(data.get("revisao_referencia_id") or "").strip() or None

        if cenario == "baseline":
            if referencia_id:
                raise ValueError("Revisão baseline não deve informar revisão de referência.")
            return

        if not referencia_id:
            raise ValueError(
                "Informe a revisão de referência para comparar economia e diffs."
            )
        if revisao_id and referencia_id == revisao_id:
            raise ValueError("A revisão não pode ser referência de si mesma.")

        referencia = self.get(referencia_id)
        if not referencia:
            raise ValueError("Revisão de referência não encontrada.")
        if str(referencia.get("instancia_id") or "") != instancia_id:
            raise ValueError("A revisão de referência deve pertencer à mesma melhoria.")

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

    def find_baseline_for_instancia(
        self,
        instancia_id: str,
        *,
        exclude_revisao_id: str | None = None,
    ) -> dict[str, Any] | None:
        if not instancia_id:
            return None
        params: list[Any] = [instancia_id]
        exclude_clause = ""
        if exclude_revisao_id:
            exclude_clause = "AND revisao_id <> %s::uuid"
            params.append(exclude_revisao_id)
        return self.fetch_one(
            f"""
            SELECT *
            FROM transformometro.revisoes
            WHERE instancia_id = %s::uuid
              AND deletado = FALSE
              AND lower(coalesce(cenario_tipo, '')) = 'baseline'
              {exclude_clause}
            ORDER BY data_inicio_vigencia DESC, versao_revisao DESC
            LIMIT 1
            """,
            tuple(params),
        )

    def find_reference_for_revisao(
        self,
        revisao_id: str,
        *,
        revisao_row: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        revisao = revisao_row or self.get(revisao_id)
        if not revisao:
            return None

        referencia_id = str(revisao.get("revisao_referencia_id") or "").strip()
        if referencia_id:
            referencia = self.get(referencia_id)
            if referencia and not referencia.get("deletado"):
                return referencia

        instancia_id = str(revisao.get("instancia_id") or "")
        return self.find_baseline_for_instancia(
            instancia_id,
            exclude_revisao_id=str(revisao.get("revisao_id") or ""),
        )
