from __future__ import annotations

from datetime import datetime
from typing import Any

from maint_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository
from maint_app.application.list_query import ListQuery, build_order_clause


class MotivoRepository(PluginBaseRepository):
    _SORT_COLUMNS = {
        "id": "motivo_id",
        "descricao": "descricao",
    }

    def list_active(self, *, filial: str) -> list[dict[str, Any]]:
        rows, _total = self.list_active_paged(filial=filial, query=ListQuery(page=1, page_size=10_000))
        return rows

    def list_active_paged(
        self,
        *,
        filial: str,
        query: ListQuery,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ["excluido = FALSE", "filial = %s"]
        params: list[Any] = [filial]
        if search and search.strip():
            where.append("descricao ILIKE %s")
            params.append(f"%{search.strip()}%")

        where_sql = " AND ".join(where)
        order = build_order_clause(query.sort_by, query.sort_dir, self._SORT_COLUMNS, "descricao")
        select_sql = f"""
            SELECT motivo_id, descricao, filial, excluir_preventiva
            FROM maintenance.motivos
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM maintenance.motivos
            WHERE {where_sql}
        """
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=tuple(params),
            page=query.page,
            page_size=query.page_size,
        )

    def create(
        self,
        descricao: str,
        *,
        filial: str,
        excluir_preventiva: bool = False,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO maintenance.motivos (descricao, filial, excluir_preventiva)
            VALUES (%s, %s, %s)
            RETURNING motivo_id, descricao, filial, excluir_preventiva
            """,
            (descricao.strip(), filial, excluir_preventiva),
        )
        return row or {}

    def update(
        self,
        motivo_id: int,
        *,
        filial: str,
        descricao: str | None = None,
        excluir_preventiva: bool | None = None,
    ) -> dict[str, Any] | None:
        fields: list[str] = ["data_alteracao = NOW()"]
        params: list[Any] = []
        if descricao is not None:
            fields.append("descricao = %s")
            params.append(descricao.strip())
        if excluir_preventiva is not None:
            fields.append("excluir_preventiva = %s")
            params.append(excluir_preventiva)
        if len(fields) == 1:
            return None

        params.extend([motivo_id, filial])
        return self.execute_returning_one(
            f"""
            UPDATE maintenance.motivos
            SET {", ".join(fields)}
            WHERE motivo_id = %s
              AND filial = %s
              AND excluido = FALSE
            RETURNING motivo_id, descricao, filial, excluir_preventiva
            """,
            tuple(params),
        )

    def soft_delete(self, motivo_id: int, *, filial: str) -> bool:
        self.execute(
            """
            UPDATE maintenance.motivos
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE motivo_id = %s
              AND filial = %s
              AND excluido = FALSE
            """,
            (motivo_id, filial),
        )
        return True


class StatusPecaRepository(PluginBaseRepository):
    _SORT_COLUMNS = {
        "status": "descricao",
        "operador": "operador",
        "percentual": "percentual",
    }

    def list_active(self, *, filial: str) -> list[dict[str, Any]]:
        rows, _total = self.list_active_paged(filial=filial, query=ListQuery(page=1, page_size=10_000))
        return rows

    def list_active_paged(
        self,
        *,
        filial: str,
        query: ListQuery,
        search: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ["excluido = FALSE", "filial = %s"]
        params: list[Any] = [filial]
        if search and search.strip():
            where.append("descricao ILIKE %s")
            params.append(f"%{search.strip()}%")

        where_sql = " AND ".join(where)
        order = build_order_clause(query.sort_by, query.sort_dir, self._SORT_COLUMNS, "percentual")
        select_sql = f"""
            SELECT status_id, descricao, operador, percentual, filial
            FROM maintenance.status_peca
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM maintenance.status_peca
            WHERE {where_sql}
        """
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=tuple(params),
            page=query.page,
            page_size=query.page_size,
        )

    def update(
        self,
        status_id: int,
        *,
        filial: str,
        descricao: str | None = None,
        operador: str | None = None,
        percentual: int | None = None,
    ) -> dict[str, Any] | None:
        row = self.fetch_one(
            """
            SELECT *
            FROM maintenance.status_peca
            WHERE status_id = %s
              AND filial = %s
              AND excluido = FALSE
            """,
            (status_id, filial),
        )
        if not row:
            return None
        return self.execute_returning_one(
            """
            UPDATE maintenance.status_peca
            SET descricao = %s,
                operador = %s,
                percentual = %s,
                data_alteracao = NOW()
            WHERE status_id = %s
              AND filial = %s
            RETURNING status_id, descricao, operador, percentual, filial
            """,
            (
                descricao if descricao is not None else row["descricao"],
                operador if operador is not None else row["operador"],
                percentual if percentual is not None else row["percentual"],
                status_id,
                filial,
            ),
        )


    def create(
        self,
        *,
        filial: str,
        descricao: str,
        operador: str,
        percentual: int,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO maintenance.status_peca (descricao, operador, percentual, filial)
            VALUES (%s, %s, %s, %s)
            RETURNING status_id, descricao, operador, percentual, filial
            """,
            (descricao.strip(), operador, percentual, filial),
        )
        return row or {}

    def soft_delete(self, status_id: int, *, filial: str) -> bool:
        self.execute(
            """
            UPDATE maintenance.status_peca
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE status_id = %s
              AND filial = %s
              AND excluido = FALSE
            """,
            (status_id, filial),
        )
        return True


class ReposicaoRepository(PluginBaseRepository):
    _PREVENTIVA_MOTIVO_JOIN = """
        INNER JOIN maintenance.motivos m_preventiva
            ON m_preventiva.motivo_id = r.motivo_id
           AND m_preventiva.excluir_preventiva = FALSE
    """

    _SORT_COLUMNS = {
        "data": "r.data_reposicao",
        "peca": "r.codigo_peca",
        "golpes": "r.golpes",
        "motivo": "m.descricao",
    }

    def list_by_ferramenta(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str | None = None,
    ) -> list[dict[str, Any]]:
        rows, _total = self.list_by_ferramenta_paged(
            filial=filial,
            codigo_ferramenta=codigo_ferramenta,
            codigo_peca=codigo_peca,
            query=ListQuery(page=1, page_size=10_000, sort_by="data", sort_dir="desc"),
        )
        return rows

    def list_preventiva_by_ferramenta(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str | None = None,
    ) -> list[dict[str, Any]]:
        where = [
            "r.excluido = FALSE",
            "r.filial = %s",
            "r.codigo_ferramenta = %s",
        ]
        params: list[Any] = [filial, codigo_ferramenta]
        if codigo_peca:
            where.append("r.codigo_peca = %s")
            params.append(codigo_peca)

        where_sql = " AND ".join(where)
        rows = self.fetch_all(
            f"""
            SELECT
                r.reposicao_id,
                r.data_reposicao,
                r.golpes
            FROM maintenance.reposicoes r
            {self._PREVENTIVA_MOTIVO_JOIN}
            WHERE {where_sql}
            ORDER BY r.data_reposicao ASC
            """,
            tuple(params),
        )
        return rows

    def list_by_ferramenta_paged(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str | None,
        motivo_id: int | None = None,
        query: ListQuery,
    ) -> tuple[list[dict[str, Any]], int]:
        where = [
            "r.excluido = FALSE",
            "r.filial = %s",
            "r.codigo_ferramenta = %s",
        ]
        params: list[Any] = [filial, codigo_ferramenta]
        if codigo_peca:
            where.append("r.codigo_peca = %s")
            params.append(codigo_peca)
        if motivo_id is not None:
            where.append("r.motivo_id = %s")
            params.append(motivo_id)

        where_sql = " AND ".join(where)
        order = build_order_clause(query.sort_by, query.sort_dir, self._SORT_COLUMNS, "data")
        select_sql = f"""
            SELECT
                r.reposicao_id,
                r.filial,
                r.codigo_ferramenta,
                r.codigo_peca,
                r.data_reposicao,
                r.data_ultima_reposicao,
                r.golpes,
                r.motivo_id,
                m.descricao AS motivo_descricao,
                r.observacao,
                r.data_criacao,
                r.data_alteracao
            FROM maintenance.reposicoes r
            INNER JOIN maintenance.motivos m ON m.motivo_id = r.motivo_id
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM maintenance.reposicoes r
            WHERE {where_sql}
        """
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=tuple(params),
            page=query.page,
            page_size=query.page_size,
        )

    def get_by_id(self, reposicao_id: str) -> dict[str, Any] | None:
        return self.fetch_one(
            """
            SELECT *
            FROM maintenance.reposicoes
            WHERE reposicao_id = %s::uuid
              AND excluido = FALSE
            """,
            (reposicao_id,),
        )

    def get_ultima_data(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
        exclude_reposicao_id: str | None = None,
    ) -> datetime | None:
        where = [
            "excluido = FALSE",
            "filial = %s",
            "codigo_ferramenta = %s",
            "codigo_peca = %s",
        ]
        params: list[Any] = [filial, codigo_ferramenta, codigo_peca]
        if exclude_reposicao_id:
            where.append("reposicao_id <> %s::uuid")
            params.append(exclude_reposicao_id)

        row = self.fetch_one(
            f"""
            SELECT data_reposicao
            FROM maintenance.reposicoes
            WHERE {' AND '.join(where)}
            ORDER BY data_reposicao DESC
            LIMIT 1
            """,
            tuple(params),
        )
        if not row:
            return None
        return row["data_reposicao"]

    def create(self, payload: dict[str, Any]) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO maintenance.reposicoes (
                filial,
                codigo_ferramenta,
                codigo_peca,
                data_reposicao,
                data_ultima_reposicao,
                golpes,
                motivo_id,
                observacao
            )
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING *
            """,
            (
                payload["filial"],
                payload["codigo_ferramenta"],
                payload["codigo_peca"],
                payload["data_reposicao"],
                payload.get("data_ultima_reposicao"),
                payload["golpes"],
                payload["motivo_id"],
                payload.get("observacao"),
            ),
        )
        return row or {}

    def update(self, reposicao_id: str, payload: dict[str, Any]) -> dict[str, Any] | None:
        return self.execute_returning_one(
            """
            UPDATE maintenance.reposicoes
            SET filial = %s,
                codigo_ferramenta = %s,
                codigo_peca = %s,
                data_reposicao = %s,
                data_ultima_reposicao = %s,
                golpes = %s,
                motivo_id = %s,
                observacao = %s,
                data_alteracao = NOW()
            WHERE reposicao_id = %s::uuid
              AND excluido = FALSE
            RETURNING *
            """,
            (
                payload["filial"],
                payload["codigo_ferramenta"],
                payload["codigo_peca"],
                payload["data_reposicao"],
                payload.get("data_ultima_reposicao"),
                payload["golpes"],
                payload["motivo_id"],
                payload.get("observacao"),
                reposicao_id,
            ),
        )

    def soft_delete(self, reposicao_id: str) -> bool:
        self.execute(
            """
            UPDATE maintenance.reposicoes
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE reposicao_id = %s::uuid
              AND excluido = FALSE
            """,
            (reposicao_id,),
        )
        return True

    def list_golpes_history(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> list[int]:
        rows = self.fetch_all(
            f"""
            SELECT r.golpes
            FROM maintenance.reposicoes r
            {self._PREVENTIVA_MOTIVO_JOIN}
            WHERE r.excluido = FALSE
              AND r.filial = %s
              AND r.codigo_ferramenta = %s
              AND r.codigo_peca = %s
            ORDER BY r.data_reposicao ASC
            """,
            (filial, codigo_ferramenta, codigo_peca),
        )
        return [int(row["golpes"]) for row in rows]

    def list_ultimas_por_par(self, *, filial: str) -> list[dict[str, Any]]:
        rows, _total = self.list_ultimas_por_par_paged(
            filial=filial,
            query=ListQuery(page=1, page_size=10_000),
        )
        return rows

    def list_ultimas_por_par_paged(
        self,
        *,
        filial: str,
        query: ListQuery,
        ferramenta: str | None = None,
        peca: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        filters = []
        filter_params: list[Any] = []
        if ferramenta and ferramenta.strip():
            filters.append("codigo_ferramenta ILIKE %s")
            filter_params.append(f"%{ferramenta.strip()}%")
        if peca and peca.strip():
            filters.append("codigo_peca ILIKE %s")
            filter_params.append(f"%{peca.strip()}%")

        filter_sql = f" AND {' AND '.join(filters)}" if filters else ""
        sort_columns = {
            "data": "data_reposicao",
            "ferramenta": "codigo_ferramenta",
            "peca": "codigo_peca",
            "golpes": "golpes",
        }
        order = build_order_clause(query.sort_by, query.sort_dir, sort_columns, "data")

        base_cte = f"""
            WITH ultimas AS (
                SELECT DISTINCT ON (r.filial, r.codigo_ferramenta, r.codigo_peca)
                    r.reposicao_id,
                    r.filial,
                    r.codigo_ferramenta,
                    r.codigo_peca,
                    r.data_reposicao,
                    r.golpes
                FROM maintenance.reposicoes r
                {self._PREVENTIVA_MOTIVO_JOIN}
                WHERE r.excluido = FALSE
                  AND r.filial = %s
                ORDER BY r.filial, r.codigo_ferramenta, r.codigo_peca, r.data_reposicao DESC
            )
        """
        params = (filial, *filter_params)
        count_sql = f"{base_cte} SELECT COUNT(1) AS total FROM ultimas WHERE 1=1{filter_sql}"
        select_sql = f"""
            {base_cte}
            SELECT reposicao_id, filial, codigo_ferramenta, codigo_peca, data_reposicao, golpes
            FROM ultimas
            WHERE 1=1{filter_sql}
            ORDER BY {order}
        """
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=params,
            page=query.page,
            page_size=query.page_size,
        )

    def media_golpes(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: str,
    ) -> float:
        row = self.fetch_one(
            f"""
            SELECT COALESCE(AVG(r.golpes), 0) AS media
            FROM maintenance.reposicoes r
            {self._PREVENTIVA_MOTIVO_JOIN}
            WHERE r.excluido = FALSE
              AND r.filial = %s
              AND r.codigo_ferramenta = %s
              AND r.codigo_peca = %s
            """,
            (filial, codigo_ferramenta, codigo_peca),
        )
        if not row:
            return 0.0
        return float(row.get("media") or 0)
