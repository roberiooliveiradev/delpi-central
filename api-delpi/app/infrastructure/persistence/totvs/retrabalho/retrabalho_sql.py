from __future__ import annotations

from app.domain.quality.retrabalho.retrabalho_view_scope import (
    FONTE_CUSTO_SEM_CUSTO,
    RETRABALHO_HORAS_IMPRODUTIVAS_VIEW,
    RETRABALHO_MOTIVO_CODE,
)
from app.infrastructure.persistence.totvs.retrabalho.retrabalho_query_settings import (
    MAX_FILTROS_ITEMS,
)

SEM_CUSTO_PREDICATE = f"LTRIM(RTRIM(FONTE_CUSTO)) = '{FONTE_CUSTO_SEM_CUSTO}'"

RANKING_ORDER_COLUMNS = {
    "horas": "total_horas",
    "custo": "total_custo",
}

DETALHES_SORT_COLUMNS = {
    "data": "DATA_REFERENCIA DESC, RECNO",
    "horas": "CAST(TEMPO_HORAS AS DECIMAL(18, 4))",
    "custo": "CAST(VALOR_PARADA_RS AS DECIMAL(18, 2))",
}


def build_base_where(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
) -> tuple[str, tuple]:
    clauses = [
        "DATA_REFERENCIA >= ?",
        "DATA_REFERENCIA <= ?",
        "LTRIM(RTRIM(FILIAL)) = ?",
        "LTRIM(RTRIM(MOTIVO)) = ?",
    ]
    params: list[str] = [start_date, end_date, branch, RETRABALHO_MOTIVO_CODE]

    if recurso:
        clauses.append("LTRIM(RTRIM(RECURSO)) = ?")
        params.append(recurso)

    if centro_custo:
        clauses.append("LTRIM(RTRIM(CENTRO_CUSTO)) = ?")
        params.append(centro_custo)

    if codigo_operador:
        clauses.append("LTRIM(RTRIM(CODIGO_OPERADOR)) = ?")
        params.append(codigo_operador)

    return " AND ".join(clauses), tuple(params)


def _from_clause() -> str:
    return f"FROM {RETRABALHO_HORAS_IMPRODUTIVAS_VIEW} WITH (NOLOCK)"


def build_health_query() -> tuple[str, tuple]:
    return (
        f"""
        SELECT TOP 1
            LTRIM(RTRIM(FILIAL)) AS filial
        {_from_clause()}
        ORDER BY DATA_REFERENCIA DESC, RECNO DESC
        """,
        (),
    )


def build_filtros_recursos_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
    )
    return (
        f"""
        SELECT TOP {MAX_FILTROS_ITEMS}
            LTRIM(RTRIM(RECURSO)) AS recurso,
            LTRIM(RTRIM(CENTRO_CUSTO)) AS centro_custo
        {_from_clause()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(RECURSO)) <> ''
        GROUP BY LTRIM(RTRIM(RECURSO)), LTRIM(RTRIM(CENTRO_CUSTO))
        ORDER BY recurso, centro_custo
        """,
        params,
    )


def build_filtros_colaboradores_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
    )
    return (
        f"""
        SELECT TOP {MAX_FILTROS_ITEMS}
            LTRIM(RTRIM(CODIGO_OPERADOR)) AS codigo_operador,
            LTRIM(RTRIM(NOME_OPERADOR)) AS nome_operador
        {_from_clause()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(CODIGO_OPERADOR)) <> ''
        GROUP BY LTRIM(RTRIM(CODIGO_OPERADOR)), LTRIM(RTRIM(NOME_OPERADOR))
        ORDER BY codigo_operador, nome_operador
        """,
        params,
    )


def build_resumo_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    return (
        f"""
        SELECT
            COUNT(*) AS total_apontamentos,
            CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas,
            CAST(SUM(CAST(VALOR_PARADA_RS AS DECIMAL(18, 2))) AS DECIMAL(18, 2)) AS total_custo,
            SUM(CASE WHEN {SEM_CUSTO_PREDICATE} THEN 1 ELSE 0 END) AS registros_sem_custo,
            CAST(
                SUM(
                    CASE
                        WHEN {SEM_CUSTO_PREDICATE}
                        THEN CAST(TEMPO_HORAS AS DECIMAL(18, 4))
                        ELSE CAST(0 AS DECIMAL(18, 4))
                    END
                ) AS DECIMAL(18, 4)
            ) AS horas_sem_custo
        {_from_clause()}
        WHERE {where_clause}
        """,
        params,
    )


def build_ranking_recurso_top1_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    return (
        f"""
        SELECT TOP 1
            LTRIM(RTRIM(RECURSO)) AS recurso,
            CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas
        {_from_clause()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(RECURSO)) <> ''
        GROUP BY LTRIM(RTRIM(RECURSO))
        ORDER BY total_horas DESC
        """,
        params,
    )


def build_ranking_colaborador_top1_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    return (
        f"""
        SELECT TOP 1
            LTRIM(RTRIM(CODIGO_OPERADOR)) AS codigo_operador,
            LTRIM(RTRIM(NOME_OPERADOR)) AS nome_operador,
            CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas
        {_from_clause()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(CODIGO_OPERADOR)) <> ''
        GROUP BY LTRIM(RTRIM(CODIGO_OPERADOR)), LTRIM(RTRIM(NOME_OPERADOR))
        ORDER BY total_horas DESC
        """,
        params,
    )


def build_mensal_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    return (
        f"""
        SELECT
            LTRIM(RTRIM(ANO_MES)) AS ano_mes,
            ANO,
            MES_NUMERO,
            LTRIM(RTRIM(MES_NOME)) AS mes_nome,
            COUNT(*) AS total_apontamentos,
            CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas,
            CAST(SUM(CAST(VALOR_PARADA_RS AS DECIMAL(18, 2))) AS DECIMAL(18, 2)) AS total_custo,
            CAST(
                SUM(
                    CASE
                        WHEN {SEM_CUSTO_PREDICATE}
                        THEN CAST(TEMPO_HORAS AS DECIMAL(18, 4))
                        ELSE CAST(0 AS DECIMAL(18, 4))
                    END
                ) AS DECIMAL(18, 4)
            ) AS horas_sem_custo
        {_from_clause()}
        WHERE {where_clause}
        GROUP BY LTRIM(RTRIM(ANO_MES)), ANO, MES_NUMERO, LTRIM(RTRIM(MES_NOME))
        ORDER BY ANO DESC, MES_NUMERO DESC
        """,
        params,
    )


def build_ranking_recursos_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
    order_by: str = "horas",
    limit: int = 10,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    order_column = RANKING_ORDER_COLUMNS.get(order_by, "total_horas")
    return (
        f"""
        SELECT TOP {int(limit)}
            LTRIM(RTRIM(RECURSO)) AS recurso,
            LTRIM(RTRIM(CENTRO_CUSTO)) AS centro_custo,
            COUNT(*) AS total_apontamentos,
            CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas,
            CAST(SUM(CAST(VALOR_PARADA_RS AS DECIMAL(18, 2))) AS DECIMAL(18, 2)) AS total_custo,
            CAST(
                SUM(
                    CASE
                        WHEN {SEM_CUSTO_PREDICATE}
                        THEN CAST(TEMPO_HORAS AS DECIMAL(18, 4))
                        ELSE CAST(0 AS DECIMAL(18, 4))
                    END
                ) AS DECIMAL(18, 4)
            ) AS horas_sem_custo
        {_from_clause()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(RECURSO)) <> ''
        GROUP BY LTRIM(RTRIM(RECURSO)), LTRIM(RTRIM(CENTRO_CUSTO))
        ORDER BY {order_column} DESC
        """,
        params,
    )


def build_ranking_colaboradores_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
    order_by: str = "horas",
    limit: int = 10,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    order_column = RANKING_ORDER_COLUMNS.get(order_by, "total_horas")
    return (
        f"""
        SELECT TOP {int(limit)}
            LTRIM(RTRIM(CODIGO_OPERADOR)) AS codigo_operador,
            LTRIM(RTRIM(NOME_OPERADOR)) AS nome_operador,
            COUNT(*) AS total_apontamentos,
            CAST(SUM(CAST(TEMPO_HORAS AS DECIMAL(18, 4))) AS DECIMAL(18, 4)) AS total_horas,
            CAST(SUM(CAST(VALOR_PARADA_RS AS DECIMAL(18, 2))) AS DECIMAL(18, 2)) AS total_custo,
            CAST(
                SUM(
                    CASE
                        WHEN {SEM_CUSTO_PREDICATE}
                        THEN CAST(TEMPO_HORAS AS DECIMAL(18, 4))
                        ELSE CAST(0 AS DECIMAL(18, 4))
                    END
                ) AS DECIMAL(18, 4)
            ) AS horas_sem_custo
        {_from_clause()}
        WHERE {where_clause}
          AND LTRIM(RTRIM(CODIGO_OPERADOR)) <> ''
        GROUP BY LTRIM(RTRIM(CODIGO_OPERADOR)), LTRIM(RTRIM(NOME_OPERADOR))
        ORDER BY {order_column} DESC
        """,
        params,
    )


def build_detalhes_count_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    return (
        f"""
        SELECT COUNT(*) AS total
        {_from_clause()}
        WHERE {where_clause}
        """,
        params,
    )


def build_detalhes_data_query(
    *,
    start_date: str,
    end_date: str,
    branch: str,
    recurso: str | None = None,
    centro_custo: str | None = None,
    codigo_operador: str | None = None,
    sort_by: str = "data",
    sort_dir: str = "desc",
    offset: int = 0,
    page_size: int = 50,
) -> tuple[str, tuple]:
    where_clause, params = build_base_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        recurso=recurso,
        centro_custo=centro_custo,
        codigo_operador=codigo_operador,
    )
    sort_column = DETALHES_SORT_COLUMNS.get(sort_by, DETALHES_SORT_COLUMNS["data"])
    direction = "ASC" if sort_dir == "asc" else "DESC"

    if sort_by == "data":
        order_clause = f"DATA_REFERENCIA {direction}, RECNO {direction}"
    else:
        order_clause = f"{sort_column} {direction}, DATA_REFERENCIA DESC, RECNO DESC"

    return (
        f"""
        SELECT
            DATA_REFERENCIA,
            LTRIM(RTRIM(FILIAL)) AS filial,
            LTRIM(RTRIM(OP)) AS op,
            LTRIM(RTRIM(PRODUTO)) AS produto,
            LTRIM(RTRIM(OPERACAO)) AS operacao,
            LTRIM(RTRIM(RECURSO)) AS recurso,
            LTRIM(RTRIM(CENTRO_CUSTO)) AS centro_custo,
            LTRIM(RTRIM(CODIGO_OPERADOR)) AS codigo_operador,
            LTRIM(RTRIM(NOME_OPERADOR)) AS nome_operador,
            CAST(TEMPO_HORAS AS DECIMAL(18, 4)) AS tempo_horas,
            CAST(VALOR_PARADA_RS AS DECIMAL(18, 2)) AS valor_parada,
            LTRIM(RTRIM(FONTE_CUSTO)) AS fonte_custo,
            LTRIM(RTRIM(MOTIVO)) AS motivo,
            LTRIM(RTRIM(OBSERVACAO)) AS observacao,
            RECNO
        {_from_clause()}
        WHERE {where_clause}
        ORDER BY {order_clause}
        OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
        """,
        (*params, int(offset), int(page_size)),
    )
