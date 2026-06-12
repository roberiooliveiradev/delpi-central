from __future__ import annotations

from datetime import datetime
from typing import Any

from maint_app.infrastructure.persistence.plugins.plugin_base_repository import PluginBaseRepository
from maint_app.application.list_query import ListQuery, build_order_clause
from maint_app.infrastructure.persistence.views import (
    VW_MOTIVOS_ATIVOS,
    VW_REPOSICOES_DETALHE,
    VW_REPOSICOES_PREVENTIVA,
    VW_REPOSICOES_ULTIMA_POR_PAR,
    VW_REVISAO_PROGRAMADA_ATIVOS,
    VW_STATUS_PECA_ATIVOS,
)


def _coerce_reposicao_date_bound(value: str | None, *, end_of_day: bool = False) -> datetime | None:
    if value is None:
        return None
    raw = str(value).strip()
    if not raw:
        return None
    if "T" in raw:
        parsed = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if parsed.tzinfo is not None:
            parsed = parsed.replace(tzinfo=None)
        return parsed
    parsed = datetime.strptime(raw[:10], "%Y-%m-%d")
    if end_of_day:
        return parsed.replace(hour=23, minute=59, second=59, microsecond=999999)
    return parsed.replace(hour=0, minute=0, second=0, microsecond=0)


class MotivoRepository(PluginBaseRepository):
    _SORT_COLUMNS = {
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
        where = ["filial = %s"]
        params: list[Any] = [filial]
        if search and search.strip():
            where.append("descricao ILIKE %s")
            params.append(f"%{search.strip()}%")

        where_sql = " AND ".join(where)
        order = build_order_clause(query.sort_by, query.sort_dir, self._SORT_COLUMNS, "descricao")
        select_sql = f"""
            SELECT motivo_id, descricao, filial, excluir_preventiva
            FROM {VW_MOTIVOS_ATIVOS}
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM {VW_MOTIVOS_ATIVOS}
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
        motivo_id: str,
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
            WHERE motivo_id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            RETURNING motivo_id, descricao, filial, excluir_preventiva
            """,
            tuple(params),
        )

    def soft_delete(self, motivo_id: str, *, filial: str) -> bool:
        self.execute(
            """
            UPDATE maintenance.motivos
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE motivo_id = %s::uuid
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
        where = ["filial = %s"]
        params: list[Any] = [filial]
        if search and search.strip():
            where.append("descricao ILIKE %s")
            params.append(f"%{search.strip()}%")

        where_sql = " AND ".join(where)
        order = build_order_clause(query.sort_by, query.sort_dir, self._SORT_COLUMNS, "percentual")
        select_sql = f"""
            SELECT status_id, descricao, operador, percentual, filial
            FROM {VW_STATUS_PECA_ATIVOS}
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM {VW_STATUS_PECA_ATIVOS}
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
        status_id: str,
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
            WHERE status_id = %s::uuid
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
            WHERE status_id = %s::uuid
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

    def soft_delete(self, status_id: str, *, filial: str) -> bool:
        self.execute(
            """
            UPDATE maintenance.status_peca
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE status_id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            """,
            (status_id, filial),
        )
        return True


class ReposicaoRepository(PluginBaseRepository):
    _SORT_COLUMNS = {
        "data": "data_reposicao",
        "peca": "codigo_peca",
        "golpes": "golpes",
        "motivo": "motivo_descricao",
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
            codigo_peca=[codigo_peca] if codigo_peca else None,
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
            "filial = %s",
            "codigo_ferramenta = %s",
        ]
        params: list[Any] = [filial, codigo_ferramenta]
        if codigo_peca:
            where.append("codigo_peca = %s")
            params.append(codigo_peca)

        where_sql = " AND ".join(where)
        rows = self.fetch_all(
            f"""
            SELECT
                reposicao_id,
                data_reposicao,
                golpes
            FROM {VW_REPOSICOES_PREVENTIVA}
            WHERE {where_sql}
            ORDER BY data_reposicao ASC
            """,
            tuple(params),
        )
        return rows

    def list_by_ferramenta_paged(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        codigo_peca: list[str] | None = None,
        motivo_ids: list[str] | None = None,
        data_inicial: str | None = None,
        data_final: str | None = None,
        query: ListQuery,
    ) -> tuple[list[dict[str, Any]], int]:
        where = [
            "filial = %s",
            "codigo_ferramenta = %s",
        ]
        params: list[Any] = [filial, codigo_ferramenta]
        if codigo_peca:
            where.append("codigo_peca = ANY(%s)")
            params.append(codigo_peca)
        if motivo_ids:
            where.append("motivo_id = ANY(%s::uuid[])")
            params.append(motivo_ids)

        start = _coerce_reposicao_date_bound(data_inicial)
        if start is not None:
            where.append("data_reposicao >= %s")
            params.append(start)

        end = _coerce_reposicao_date_bound(data_final, end_of_day=True)
        if end is not None:
            where.append("data_reposicao <= %s")
            params.append(end)

        where_sql = " AND ".join(where)
        order = build_order_clause(query.sort_by, query.sort_dir, self._SORT_COLUMNS, "data")
        select_sql = f"""
            SELECT
                reposicao_id,
                filial,
                codigo_ferramenta,
                codigo_peca,
                data_reposicao,
                data_ultima_reposicao,
                golpes,
                motivo_id,
                motivo_descricao,
                observacao,
                data_criacao,
                data_alteracao
            FROM {VW_REPOSICOES_DETALHE}
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM {VW_REPOSICOES_DETALHE}
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
            SELECT golpes
            FROM {VW_REPOSICOES_PREVENTIVA}
            WHERE filial = %s
              AND codigo_ferramenta = %s
              AND codigo_peca = %s
            ORDER BY data_reposicao ASC
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

        params = (filial, *filter_params)
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM {VW_REPOSICOES_ULTIMA_POR_PAR}
            WHERE filial = %s{filter_sql}
        """
        select_sql = f"""
            SELECT reposicao_id, filial, codigo_ferramenta, codigo_peca, data_reposicao, golpes
            FROM {VW_REPOSICOES_ULTIMA_POR_PAR}
            WHERE filial = %s{filter_sql}
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
            SELECT COALESCE(AVG(golpes), 0) AS media
            FROM {VW_REPOSICOES_PREVENTIVA}
            WHERE filial = %s
              AND codigo_ferramenta = %s
              AND codigo_peca = %s
            """,
            (filial, codigo_ferramenta, codigo_peca),
        )
        if not row:
            return 0.0
        return float(row.get("media") or 0)

    def map_ultima_reposicao_por_ferramenta(self, *, filial: str) -> dict[str, datetime]:
        rows = self.fetch_all(
            """
            SELECT codigo_ferramenta, MAX(data_reposicao) AS data_reposicao
            FROM maintenance.reposicoes
            WHERE excluido = FALSE
              AND filial = %s
            GROUP BY codigo_ferramenta
            """,
            (filial,),
        )
        result: dict[str, datetime] = {}
        for row in rows:
            codigo = str(row["codigo_ferramenta"])
            data = row.get("data_reposicao")
            if isinstance(data, datetime):
                result[codigo] = data
        return result


class RevisaoProgramadaRepository(PluginBaseRepository):
    _SORT_COLUMNS = {
        "ferramenta": "codigo_ferramenta",
        "intervalo": "intervalo_meses",
        "ultima": "data_ultima_revisao",
    }

    def list_active(self, *, filial: str) -> list[dict[str, Any]]:
        rows, _total = self.list_active_paged(
            filial=filial,
            query=ListQuery(page=1, page_size=10_000, sort_by="ferramenta", sort_dir="asc"),
        )
        return rows

    def list_active_paged(
        self,
        *,
        filial: str,
        query: ListQuery,
        search: str | None = None,
        codigo_ferramenta: str | None = None,
    ) -> tuple[list[dict[str, Any]], int]:
        where = ["filial = %s"]
        params: list[Any] = [filial]
        if codigo_ferramenta and codigo_ferramenta.strip():
            where.append("codigo_ferramenta = %s")
            params.append(codigo_ferramenta.strip().upper())
        elif search and search.strip():
            where.append("codigo_ferramenta ILIKE %s")
            params.append(f"%{search.strip()}%")

        where_sql = " AND ".join(where)
        order = build_order_clause(query.sort_by, query.sort_dir, self._SORT_COLUMNS, "ferramenta")
        select_sql = f"""
            SELECT
                revisao_id,
                filial,
                codigo_ferramenta,
                intervalo_meses,
                data_ultima_revisao,
                observacao,
                data_criacao,
                data_alteracao
            FROM {VW_REVISAO_PROGRAMADA_ATIVOS}
            WHERE {where_sql}
            ORDER BY {order}
        """
        count_sql = f"""
            SELECT COUNT(1) AS total
            FROM {VW_REVISAO_PROGRAMADA_ATIVOS}
            WHERE {where_sql}
        """
        return self.fetch_paged(
            select_sql=select_sql,
            count_sql=count_sql,
            params=tuple(params),
            page=query.page,
            page_size=query.page_size,
        )

    def exists_active(self, *, filial: str, codigo_ferramenta: str) -> bool:
        row = self.fetch_one(
            f"""
            SELECT 1
            FROM {VW_REVISAO_PROGRAMADA_ATIVOS}
            WHERE filial = %s
              AND codigo_ferramenta = %s
            LIMIT 1
            """,
            (filial, codigo_ferramenta.strip().upper()),
        )
        return row is not None

    def get_by_id(self, revisao_id: str, *, filial: str) -> dict[str, Any] | None:
        return self.fetch_one(
            f"""
            SELECT *
            FROM {VW_REVISAO_PROGRAMADA_ATIVOS}
            WHERE revisao_id = %s::uuid
              AND filial = %s
            """,
            (revisao_id, filial),
        )

    def create(
        self,
        *,
        filial: str,
        codigo_ferramenta: str,
        intervalo_meses: int,
        observacao: str | None = None,
        data_ultima_revisao: str | datetime | None = None,
    ) -> dict[str, Any]:
        row = self.execute_returning_one(
            """
            INSERT INTO maintenance.revisao_programada (
                filial,
                codigo_ferramenta,
                intervalo_meses,
                observacao,
                data_ultima_revisao
            )
            VALUES (%s, %s, %s, %s, %s)
            RETURNING
                revisao_id,
                filial,
                codigo_ferramenta,
                intervalo_meses,
                data_ultima_revisao,
                observacao,
                data_criacao,
                data_alteracao
            """,
            (
                filial,
                codigo_ferramenta.strip().upper(),
                intervalo_meses,
                observacao.strip() if observacao else None,
                _coerce_reposicao_date_bound(str(data_ultima_revisao)) if data_ultima_revisao else None,
            ),
        )
        return row or {}

    def update(
        self,
        revisao_id: str,
        *,
        filial: str,
        intervalo_meses: int | None = None,
        observacao: str | None = None,
        data_ultima_revisao: str | datetime | None = None,
        update_data_ultima_revisao: bool = False,
    ) -> dict[str, Any] | None:
        fields: list[str] = ["data_alteracao = NOW()"]
        params: list[Any] = []
        if intervalo_meses is not None:
            fields.append("intervalo_meses = %s")
            params.append(intervalo_meses)
        if observacao is not None:
            fields.append("observacao = %s")
            params.append(observacao.strip() or None)
        if update_data_ultima_revisao:
            parsed = (
                _coerce_reposicao_date_bound(str(data_ultima_revisao))
                if data_ultima_revisao
                else None
            )
            fields.append("data_ultima_revisao = %s")
            params.append(parsed)
        if len(fields) == 1:
            return self.get_by_id(revisao_id, filial=filial)

        params.extend([revisao_id, filial])
        return self.execute_returning_one(
            f"""
            UPDATE maintenance.revisao_programada
            SET {", ".join(fields)}
            WHERE revisao_id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            RETURNING
                revisao_id,
                filial,
                codigo_ferramenta,
                intervalo_meses,
                data_ultima_revisao,
                observacao,
                data_criacao,
                data_alteracao
            """,
            tuple(params),
        )

    def registrar_revisao(
        self,
        revisao_id: str,
        *,
        filial: str,
        data_revisao: str | datetime | None = None,
    ) -> dict[str, Any] | None:
        if data_revisao:
            parsed = _coerce_reposicao_date_bound(str(data_revisao))
            return self.execute_returning_one(
                """
                UPDATE maintenance.revisao_programada
                SET data_ultima_revisao = %s,
                    data_alteracao = NOW()
                WHERE revisao_id = %s::uuid
                  AND filial = %s
                  AND excluido = FALSE
                RETURNING
                    revisao_id,
                    filial,
                    codigo_ferramenta,
                    intervalo_meses,
                    data_ultima_revisao,
                    observacao,
                    data_criacao,
                    data_alteracao
                """,
                (parsed, revisao_id, filial),
            )
        return self.execute_returning_one(
            """
            UPDATE maintenance.revisao_programada
            SET data_ultima_revisao = NOW(),
                data_alteracao = NOW()
            WHERE revisao_id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            RETURNING
                revisao_id,
                filial,
                codigo_ferramenta,
                intervalo_meses,
                data_ultima_revisao,
                observacao,
                data_criacao,
                data_alteracao
            """,
            (revisao_id, filial),
        )

    def soft_delete(self, revisao_id: str, *, filial: str) -> bool:
        self.execute(
            """
            UPDATE maintenance.revisao_programada
            SET excluido = TRUE,
                data_alteracao = NOW()
            WHERE revisao_id = %s::uuid
              AND filial = %s
              AND excluido = FALSE
            """,
            (revisao_id, filial),
        )
        return True
