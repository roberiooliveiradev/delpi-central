from __future__ import annotations

from typing import Any

from maint_app.application.list_query import ListQuery, build_order_clause
from maint_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

_RETURNING = """
    id,
    filial,
    codigo_intermediario,
    descricao_intermediario,
    codigo_produto_acabado,
    codigo_ct_corte,
    nome_programa,
    observacao,
    ativo,
    usuario_sub,
    usuario_ativacao_sub,
    usuario_ativacao_nome,
    data_ativacao,
    data_criacao,
    data_alteracao
"""


class ProgramasMaquinaProdutosRepository(PluginBaseRepository):
    _SORT_COLUMNS = {
        "codigo_intermediario": "codigo_intermediario",
        "descricao_intermediario": "descricao_intermediario",
        "codigo_produto_acabado": "codigo_produto_acabado",
        "codigo_ct_corte": "codigo_ct_corte",
        "data_ativacao": "data_ativacao",
        "usuario_ativacao_nome": "usuario_ativacao_nome",
        "data_alteracao": "data_alteracao",
        "ativo": "ativo",
    }

    def list_active_codes(self, *, filial: str) -> set[str]:
        rows = self.fetch_all(
            """
            SELECT codigo_intermediario
            FROM maintenance.programas_maquina_produtos
            WHERE filial = %s
              AND excluido = FALSE
              AND ativo = TRUE
            """,
            (filial,),
        )
        return {
            str(row.get("codigo_intermediario") or "").strip()
            for row in rows
            if str(row.get("codigo_intermediario") or "").strip()
        }

    def list_paged(
        self,
        *,
        filial: str,
        query: ListQuery,
        search: str | None = None,
        apenas_ativos: bool = True,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ["filial = %s", "excluido = FALSE"]
        params: list[Any] = [filial]
        if apenas_ativos:
            where.append("ativo = TRUE")
        if search and search.strip():
            where.append(
                """
                (
                    codigo_intermediario ILIKE %s
                    OR COALESCE(descricao_intermediario, '') ILIKE %s
                    OR COALESCE(codigo_produto_acabado, '') ILIKE %s
                    OR COALESCE(usuario_ativacao_nome, '') ILIKE %s
                )
                """
            )
            like = f"%{search.strip()}%"
            params.extend([like, like, like, like])

        where_sql = " AND ".join(where)
        order = build_order_clause(
            query.sort_by,
            query.sort_dir,
            self._SORT_COLUMNS,
            "codigo_intermediario",
        )
        select_sql = f"""
            SELECT {_RETURNING}
            FROM maintenance.programas_maquina_produtos
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM maintenance.programas_maquina_produtos
            WHERE {where_sql}
        """
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=tuple(params),
            page=query.page,
            page_size=query.page_size,
        )

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        ativo = bool(payload.get("ativo", True))
        row = self.execute_returning_one(
            f"""
            INSERT INTO maintenance.programas_maquina_produtos (
                filial,
                codigo_intermediario,
                descricao_intermediario,
                codigo_produto_acabado,
                codigo_ct_corte,
                nome_programa,
                observacao,
                ativo,
                usuario_sub,
                usuario_ativacao_sub,
                usuario_ativacao_nome,
                data_ativacao
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                CASE WHEN %s THEN NOW() ELSE NULL END
            )
            RETURNING {_RETURNING}
            """,
            (
                payload["filial"],
                payload["codigo_intermediario"],
                payload.get("descricao_intermediario"),
                payload.get("codigo_produto_acabado"),
                payload.get("codigo_ct_corte"),
                payload.get("nome_programa"),
                payload.get("observacao"),
                ativo,
                payload.get("usuario_sub"),
                payload.get("usuario_ativacao_sub") if ativo else None,
                payload.get("usuario_ativacao_nome") if ativo else None,
                ativo,
            ),
        )
        return row or {}

    def update(
        self,
        item_id: str,
        *,
        filial: str,
        nome_programa: str | None = None,
        observacao: str | None = None,
        ativo: bool | None = None,
        codigo_produto_acabado: str | None = None,
        codigo_ct_corte: str | None = None,
        descricao_intermediario: str | None = None,
        usuario_ativacao_sub: str | None = None,
        usuario_ativacao_nome: str | None = None,
    ) -> dict[str, Any] | None:
        current = self.execute_returning_one(
            f"""
            SELECT {_RETURNING}
            FROM maintenance.programas_maquina_produtos
            WHERE id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            """,
            (item_id, filial),
        )
        if not current:
            return None

        was_active = bool(current.get("ativo"))
        next_ativo = ativo if ativo is not None else was_active
        activating = next_ativo and not was_active

        next_nome = (
            nome_programa
            if nome_programa is not None
            else current.get("nome_programa")
        )
        next_obs = observacao if observacao is not None else current.get("observacao")
        next_pa = (
            codigo_produto_acabado
            if codigo_produto_acabado is not None
            else current.get("codigo_produto_acabado")
        )
        next_ct = (
            codigo_ct_corte
            if codigo_ct_corte is not None
            else current.get("codigo_ct_corte")
        )
        next_desc = (
            descricao_intermediario
            if descricao_intermediario is not None
            else current.get("descricao_intermediario")
        )

        if activating:
            next_data_ativacao_sql = "NOW()"
            next_user_sub = usuario_ativacao_sub
            next_user_nome = usuario_ativacao_nome
        else:
            next_data_ativacao_sql = "data_ativacao"
            next_user_sub = current.get("usuario_ativacao_sub")
            next_user_nome = current.get("usuario_ativacao_nome")

        return self.execute_returning_one(
            f"""
            UPDATE maintenance.programas_maquina_produtos
            SET
                nome_programa = %s,
                observacao = %s,
                ativo = %s,
                codigo_produto_acabado = %s,
                codigo_ct_corte = %s,
                descricao_intermediario = %s,
                usuario_ativacao_sub = %s,
                usuario_ativacao_nome = %s,
                data_ativacao = {next_data_ativacao_sql},
                data_alteracao = NOW()
            WHERE id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            RETURNING {_RETURNING}
            """,
            (
                next_nome,
                next_obs,
                next_ativo,
                next_pa,
                next_ct,
                next_desc,
                next_user_sub,
                next_user_nome,
                item_id,
                filial,
            ),
        )

    def soft_delete(self, item_id: str, *, filial: str) -> bool:
        row = self.execute_returning_one(
            """
            UPDATE maintenance.programas_maquina_produtos
            SET excluido = TRUE, ativo = FALSE, data_alteracao = NOW()
            WHERE id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            RETURNING id
            """,
            (item_id, filial),
        )
        return bool(row)
