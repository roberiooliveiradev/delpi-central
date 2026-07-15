from __future__ import annotations

from app.application.dto.financeiro_inadimplencia.constantes import MAX_PAGE_SIZE

INADIMPLENCIA_VIEW = "dbo.VW_FINANCEIRO_INADIMPLENCIA"

CLIENTES_SEARCH_FIELDS = (
    "CLIENTE",
    "NOME_CLIENTE",
    "NOME_REDUZIDO",
)

TITULOS_SEARCH_FIELDS = (
    "NUMERO",
    "PREFIXO",
    "CLIENTE",
    "NOME_CLIENTE",
    "NOME_REDUZIDO",
)

CLIENTES_SORT_BY_SQL_COLUMNS = {
    "late_amount": "valor_atraso",
    "late_titles": "titulos_atraso",
    "total_amount": "valor_total",
    "on_time_by_quantity_percent": "percentual_em_dia_qtd",
    "on_time_by_amount_percent": "percentual_em_dia_valor",
    "customer_name": "nome_cliente",
}

TITULOS_SORT_BY_SQL_COLUMNS = {
    "amount": "CAST(VALOR_TITULO AS DECIMAL(18, 2))",
    "days_late": "DIAS_ATRASO",
    "payment_date": "DATA_BAIXA",
    "issue_date": "DATA_EMISSAO",
    "customer_name": "LTRIM(RTRIM(NOME_CLIENTE))",
    "number": "LTRIM(RTRIM(NUMERO))",
}

TITULOS_SELECT = """
    LTRIM(RTRIM(FILIAL)) AS filial,
    LTRIM(RTRIM(PREFIXO)) AS prefixo,
    LTRIM(RTRIM(NUMERO)) AS numero,
    LTRIM(RTRIM(PARCELA)) AS parcela,
    LTRIM(RTRIM(TIPO)) AS tipo,
    LTRIM(RTRIM(CLIENTE)) AS cliente_codigo,
    LTRIM(RTRIM(LOJA)) AS loja,
    LTRIM(RTRIM(NOME_CLIENTE)) AS nome_cliente,
    LTRIM(RTRIM(NOME_REDUZIDO)) AS nome_reduzido,
    DATA_EMISSAO AS data_emissao,
    DATA_VENCIMENTO_REAL AS data_vencimento_real,
    DATA_BAIXA AS data_baixa,
    CAST(VALOR_TITULO AS DECIMAL(18, 2)) AS valor_titulo,
    PAGO_EM_DIA AS pago_em_dia,
    DIAS_ATRASO AS dias_atraso,
    LTRIM(RTRIM(FAIXA_ATRASO)) AS faixa_atraso
""".strip()


def build_period_where(
    *,
    start_date: str,
    end_date_exclusive: str,
) -> tuple[str, tuple]:
    return (
        "MES_REFERENCIA >= ? AND MES_REFERENCIA < ?",
        (start_date, end_date_exclusive),
    )


def _build_search_clause(
    search: str | None,
    fields: tuple[str, ...],
) -> tuple[str, tuple]:
    normalized = str(search or "").strip()
    if not normalized:
        return "", ()

    comparisons = " OR ".join(
        f"LTRIM(RTRIM({field})) COLLATE Latin1_General_CI_AI LIKE ?"
        for field in fields
    )
    pattern = f"%{normalized}%"
    return f"({comparisons})", tuple([pattern] * len(fields))


def build_resumo_query(
    *,
    start_date: str,
    end_date_exclusive: str,
) -> tuple[str, tuple]:
    where_clause, params = build_period_where(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
    )
    query = f"""
SELECT
    COUNT(*) AS titulos,
    COALESCE(SUM(PAGO_EM_DIA), 0) AS titulos_em_dia,
    COALESCE(SUM(PAGO_COM_ATRASO), 0) AS titulos_atraso,
    COALESCE(SUM(CAST(VALOR_TITULO AS DECIMAL(18, 2))), 0) AS valor_total,
    COALESCE(
        SUM(
            CASE
                WHEN PAGO_EM_DIA = 1 THEN CAST(VALOR_TITULO AS DECIMAL(18, 2))
                ELSE 0
            END
        ),
        0
    ) AS valor_em_dia,
    COALESCE(
        SUM(
            CASE
                WHEN PAGO_COM_ATRASO = 1 THEN CAST(VALOR_TITULO AS DECIMAL(18, 2))
                ELSE 0
            END
        ),
        0
    ) AS valor_atraso
FROM {INADIMPLENCIA_VIEW} WITH (NOLOCK)
WHERE {where_clause}
""".strip()
    return query, params


def build_mensal_query(
    *,
    start_date: str,
    end_date_exclusive: str,
    customer_code: str | None = None,
    store_code: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params_period = build_period_where(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
    )
    params: list = list(params_period)

    if customer_code:
        where_clause = f"{where_clause} AND LTRIM(RTRIM(CLIENTE)) = ?"
        params.append(customer_code)

    if store_code:
        where_clause = f"{where_clause} AND LTRIM(RTRIM(LOJA)) = ?"
        params.append(store_code)

    query = f"""
SELECT
    MES_REFERENCIA AS mes,
    COUNT(*) AS total_titulos,
    COALESCE(SUM(PAGO_EM_DIA), 0) AS titulos_em_dia,
    COALESCE(SUM(PAGO_COM_ATRASO), 0) AS titulos_atraso,
    COALESCE(SUM(CAST(VALOR_TITULO AS DECIMAL(18, 2))), 0) AS valor_total,
    COALESCE(
        SUM(
            CASE
                WHEN PAGO_EM_DIA = 1 THEN CAST(VALOR_TITULO AS DECIMAL(18, 2))
                ELSE 0
            END
        ),
        0
    ) AS valor_em_dia,
    COALESCE(
        SUM(
            CASE
                WHEN PAGO_COM_ATRASO = 1 THEN CAST(VALOR_TITULO AS DECIMAL(18, 2))
                ELSE 0
            END
        ),
        0
    ) AS valor_atraso
FROM {INADIMPLENCIA_VIEW} WITH (NOLOCK)
WHERE {where_clause}
GROUP BY MES_REFERENCIA
ORDER BY MES_REFERENCIA ASC
""".strip()
    return query, tuple(params)


def build_faixas_atraso_query(
    *,
    start_date: str,
    end_date_exclusive: str,
) -> tuple[str, tuple]:
    where_clause, params = build_period_where(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
    )
    query = f"""
SELECT
    LTRIM(RTRIM(FAIXA_ATRASO)) AS codigo,
    COUNT(*) AS quantidade,
    COALESCE(SUM(CAST(VALOR_TITULO AS DECIMAL(18, 2))), 0) AS valor
FROM {INADIMPLENCIA_VIEW} WITH (NOLOCK)
WHERE {where_clause}
GROUP BY LTRIM(RTRIM(FAIXA_ATRASO))
""".strip()
    return query, params


def _build_clientes_cte(
    *,
    start_date: str,
    end_date_exclusive: str,
    q: str | None = None,
    only_with_delays: bool = True,
) -> tuple[str, tuple]:
    where_clause, params = build_period_where(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
    )
    search_clause, search_params = _build_search_clause(q, CLIENTES_SEARCH_FIELDS)
    if search_clause:
        where_clause = f"{where_clause} AND {search_clause}"
        params = params + search_params

    having_clause = ""
    if only_with_delays:
        having_clause = "HAVING COALESCE(SUM(PAGO_COM_ATRASO), 0) > 0"

    cte = f"""
WITH grouped AS (
    SELECT
        LTRIM(RTRIM(CLIENTE)) AS cliente_codigo,
        LTRIM(RTRIM(LOJA)) AS loja,
        MAX(LTRIM(RTRIM(NOME_CLIENTE))) AS nome_cliente,
        MAX(LTRIM(RTRIM(NOME_REDUZIDO))) AS nome_reduzido,
        COUNT(*) AS total_titulos,
        COALESCE(SUM(PAGO_EM_DIA), 0) AS titulos_em_dia,
        COALESCE(SUM(PAGO_COM_ATRASO), 0) AS titulos_atraso,
        COALESCE(SUM(CAST(VALOR_TITULO AS DECIMAL(18, 2))), 0) AS valor_total,
        COALESCE(
            SUM(
                CASE
                    WHEN PAGO_COM_ATRASO = 1 THEN CAST(VALOR_TITULO AS DECIMAL(18, 2))
                    ELSE 0
                END
            ),
            0
        ) AS valor_atraso,
        CASE
            WHEN COUNT(*) > 0
            THEN ROUND(COALESCE(SUM(PAGO_EM_DIA), 0) * 100.0 / COUNT(*), 2)
            ELSE 0
        END AS percentual_em_dia_qtd,
        CASE
            WHEN COALESCE(SUM(CAST(VALOR_TITULO AS DECIMAL(18, 2))), 0) > 0
            THEN ROUND(
                COALESCE(
                    SUM(
                        CASE
                            WHEN PAGO_EM_DIA = 1
                            THEN CAST(VALOR_TITULO AS DECIMAL(18, 2))
                            ELSE 0
                        END
                    ),
                    0
                ) * 100.0 / SUM(CAST(VALOR_TITULO AS DECIMAL(18, 2))),
                2
            )
            ELSE 0
        END AS percentual_em_dia_valor
    FROM {INADIMPLENCIA_VIEW} WITH (NOLOCK)
    WHERE {where_clause}
    GROUP BY LTRIM(RTRIM(CLIENTE)), LTRIM(RTRIM(LOJA))
    {having_clause}
)
""".strip()
    return cte, params


def resolve_clientes_order_by(*, sort_by: str, sort_dir: str) -> str:
    column = CLIENTES_SORT_BY_SQL_COLUMNS.get(sort_by)
    if column is None:
        raise ValueError(f"sort_by inválido: {sort_by!r}")

    direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"
    # Tie-breakers sem repetir a coluna principal (SQL Server rejeita ORDER BY duplicado).
    tie_breakers = [
        "nome_cliente ASC",
        "cliente_codigo ASC",
        "loja ASC",
    ]
    primary = f"{column} {direction}"
    extras = [item for item in tie_breakers if not item.startswith(f"{column} ")]
    return ", ".join([primary, *extras])


def build_clientes_count_query(
    *,
    start_date: str,
    end_date_exclusive: str,
    q: str | None = None,
    only_with_delays: bool = True,
) -> tuple[str, tuple]:
    cte, params = _build_clientes_cte(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        q=q,
        only_with_delays=only_with_delays,
    )
    query = f"""
{cte}
SELECT COUNT(*) AS total_items
FROM grouped
""".strip()
    return query, params


def build_clientes_data_query(
    *,
    start_date: str,
    end_date_exclusive: str,
    q: str | None = None,
    only_with_delays: bool = True,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> tuple[str, tuple]:
    cte, params = _build_clientes_cte(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        q=q,
        only_with_delays=only_with_delays,
    )
    order_by = resolve_clientes_order_by(sort_by=sort_by, sort_dir=sort_dir)
    safe_page = max(int(page), 1)
    safe_page_size = min(max(int(page_size), 1), MAX_PAGE_SIZE)
    offset = (safe_page - 1) * safe_page_size
    query = f"""
{cte}
SELECT
    cliente_codigo,
    loja,
    nome_cliente,
    nome_reduzido,
    total_titulos,
    titulos_em_dia,
    titulos_atraso,
    valor_total,
    valor_atraso,
    percentual_em_dia_qtd,
    percentual_em_dia_valor
FROM grouped
ORDER BY {order_by}
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
""".strip()
    return query, params + (offset, safe_page_size)


def build_titulos_where(
    *,
    start_date: str,
    end_date_exclusive: str,
    customer_code: str | None = None,
    store_code: str | None = None,
    status: str = "all",
    delay_range: str | None = None,
    q: str | None = None,
) -> tuple[str, tuple]:
    where_clause, period_params = build_period_where(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
    )
    params: list = list(period_params)

    if customer_code:
        where_clause = f"{where_clause} AND LTRIM(RTRIM(CLIENTE)) = ?"
        params.append(customer_code)

    if store_code:
        where_clause = f"{where_clause} AND LTRIM(RTRIM(LOJA)) = ?"
        params.append(store_code)

    normalized_status = str(status or "all").strip().lower()
    if normalized_status == "on_time":
        where_clause = f"{where_clause} AND PAGO_EM_DIA = 1"
    elif normalized_status == "late":
        where_clause = f"{where_clause} AND PAGO_COM_ATRASO = 1"

    if delay_range:
        where_clause = (
            f"{where_clause} AND LTRIM(RTRIM(FAIXA_ATRASO)) = ?"
        )
        params.append(delay_range)

    search_clause, search_params = _build_search_clause(q, TITULOS_SEARCH_FIELDS)
    if search_clause:
        where_clause = f"{where_clause} AND {search_clause}"
        params.extend(search_params)

    return where_clause, tuple(params)


def resolve_titulos_order_by(*, sort_by: str, sort_dir: str) -> str:
    column = TITULOS_SORT_BY_SQL_COLUMNS.get(sort_by)
    if column is None:
        raise ValueError(f"sort_by inválido: {sort_by!r}")

    direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"
    # Tie-breakers sem repetir a coluna principal (SQL Server rejeita ORDER BY duplicado).
    tie_breakers = [
        "DIAS_ATRASO DESC",
        "DATA_BAIXA DESC",
        "LTRIM(RTRIM(PREFIXO)) ASC",
        "LTRIM(RTRIM(NUMERO)) ASC",
        "LTRIM(RTRIM(PARCELA)) ASC",
    ]
    primary = f"{column} {direction}"
    extras = [item for item in tie_breakers if not item.startswith(f"{column} ")]
    return ", ".join([primary, *extras])


def build_titulos_count_query(
    *,
    start_date: str,
    end_date_exclusive: str,
    customer_code: str | None = None,
    store_code: str | None = None,
    status: str = "all",
    delay_range: str | None = None,
    q: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_titulos_where(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        customer_code=customer_code,
        store_code=store_code,
        status=status,
        delay_range=delay_range,
        q=q,
    )
    query = f"""
SELECT COUNT(*) AS total_items
FROM {INADIMPLENCIA_VIEW} WITH (NOLOCK)
WHERE {where_clause}
""".strip()
    return query, params


def build_titulos_data_query(
    *,
    start_date: str,
    end_date_exclusive: str,
    customer_code: str | None = None,
    store_code: str | None = None,
    status: str = "all",
    delay_range: str | None = None,
    q: str | None = None,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> tuple[str, tuple]:
    where_clause, params = build_titulos_where(
        start_date=start_date,
        end_date_exclusive=end_date_exclusive,
        customer_code=customer_code,
        store_code=store_code,
        status=status,
        delay_range=delay_range,
        q=q,
    )
    order_by = resolve_titulos_order_by(sort_by=sort_by, sort_dir=sort_dir)
    safe_page = max(int(page), 1)
    safe_page_size = min(max(int(page_size), 1), MAX_PAGE_SIZE)
    offset = (safe_page - 1) * safe_page_size
    query = f"""
SELECT
    {TITULOS_SELECT}
FROM {INADIMPLENCIA_VIEW} WITH (NOLOCK)
WHERE {where_clause}
ORDER BY {order_by}
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
""".strip()
    return query, params + (offset, safe_page_size)
