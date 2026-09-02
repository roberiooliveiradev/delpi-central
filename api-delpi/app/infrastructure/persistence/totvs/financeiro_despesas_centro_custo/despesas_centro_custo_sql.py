from __future__ import annotations

DESPESAS_CENTRO_CUSTO_VIEW = "dbo.vw_fin_despesas_centro_custo"

# tipo_produto_lancamento na view — MP = matéria-prima (suprimentos).
RAW_MATERIAL_PRODUCT_TYPE = "MP"

# Teto inicial para fornecedores distintos no /filtros — evita payload grande.
MAX_FORNECEDORES_FILTROS = 500

DEFAULT_RANKING_LIMIT = 10
MAX_RANKING_LIMIT = 50

DEFAULT_PAGE_SIZE = 50
MAX_PAGE_SIZE = 200

SEARCH_FIELDS = (
    "documento",
    "pedido",
    "produto_codigo",
    "produto_descricao",
    "observacoes",
    "razao_social",
    "centro_custo_codigo",
    "centro_custo_descricao",
)

SORT_BY_SQL_COLUMNS = {
    "data_emissao": "LTRIM(RTRIM(data_emissao))",
    "documento": "LTRIM(RTRIM(documento))",
    "razao_social": "LTRIM(RTRIM(razao_social))",
    "centro_custo_codigo": "LTRIM(RTRIM(centro_custo_codigo))",
    "centro_custo_descricao": "LTRIM(RTRIM(centro_custo_descricao))",
    "produto_codigo": "LTRIM(RTRIM(produto_codigo))",
    "produto_descricao": "LTRIM(RTRIM(produto_descricao))",
    "valor_total": "CAST(valor_total AS DECIMAL(18, 2))",
}

LANCAMENTOS_SELECT = """
    LTRIM(RTRIM(filial)) AS filial,
    LTRIM(RTRIM(data_emissao)) AS data_emissao,
    LTRIM(RTRIM(data_emissao_formatada)) AS data_emissao_formatada,
    LTRIM(RTRIM(centro_custo_codigo)) AS centro_custo_codigo,
    LTRIM(RTRIM(centro_custo_descricao)) AS centro_custo_descricao,
    LTRIM(RTRIM(fornecedor_cliente_codigo)) AS fornecedor_cliente_codigo,
    LTRIM(RTRIM(loja)) AS loja,
    LTRIM(RTRIM(razao_social)) AS razao_social,
    LTRIM(RTRIM(documento)) AS documento,
    LTRIM(RTRIM(serie)) AS serie,
    LTRIM(RTRIM(pedido)) AS pedido,
    LTRIM(RTRIM(item)) AS item,
    LTRIM(RTRIM(item_pedido)) AS item_pedido,
    LTRIM(RTRIM(produto_codigo)) AS produto_codigo,
    LTRIM(RTRIM(produto_descricao)) AS produto_descricao,
    LTRIM(RTRIM(observacoes)) AS observacoes,
    CAST(quantidade AS DECIMAL(18, 4)) AS quantidade,
    CAST(valor_unitario AS DECIMAL(18, 4)) AS valor_unitario,
    CAST(valor_total AS DECIMAL(18, 2)) AS valor_total,
    LTRIM(RTRIM(conta_contabil)) AS conta_contabil,
    LTRIM(RTRIM(rateio)) AS rateio,
    LTRIM(RTRIM(tes)) AS tes,
    LTRIM(RTRIM(cfop)) AS cfop,
    LTRIM(RTRIM(tipo_documento)) AS tipo_documento,
    LTRIM(RTRIM(tipo_produto_lancamento)) AS tipo_produto_lancamento,
    recno_sd1
""".strip()


def build_query_where(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    clauses = ["data_emissao BETWEEN ? AND ?"]
    params: list[str] = [start_date, end_date]

    if branch:
        clauses.append("LTRIM(RTRIM(filial)) = ?")
        params.append(branch)

    if cost_center:
        clauses.append("LTRIM(RTRIM(centro_custo_codigo)) = ?")
        params.append(cost_center)

    if supplier_code:
        clauses.append("LTRIM(RTRIM(fornecedor_cliente_codigo)) = ?")
        params.append(supplier_code)

    if supplier_store:
        clauses.append("LTRIM(RTRIM(loja)) = ?")
        params.append(supplier_store)

    if exclude_mp_products:
        clauses.append("UPPER(LTRIM(RTRIM(tipo_produto_lancamento))) <> ?")
        params.append(RAW_MATERIAL_PRODUCT_TYPE)

    return " AND ".join(clauses), tuple(params)


def _build_search_clause(search: str | None) -> tuple[str, tuple]:
    normalized = str(search or "").strip()
    if not normalized:
        return "", ()

    comparisons = " OR ".join(
        f"LTRIM(RTRIM({field})) COLLATE Latin1_General_CI_AI LIKE ?"
        for field in SEARCH_FIELDS
    )
    pattern = f"%{normalized}%"
    return f"({comparisons})", tuple([pattern] * len(SEARCH_FIELDS))


def build_lancamentos_where(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
    search: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    where_clause, params = build_query_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        exclude_mp_products=exclude_mp_products,
    )
    search_clause, search_params = _build_search_clause(search)
    if not search_clause:
        return where_clause, params

    return f"{where_clause} AND {search_clause}", params + search_params


def resolve_lancamentos_order_by(*, sort_by: str, sort_dir: str) -> str:
    column = SORT_BY_SQL_COLUMNS.get(sort_by)
    if column is None:
        raise ValueError(f"sort_by inválido: {sort_by!r}")

    direction = "ASC" if str(sort_dir).lower() == "asc" else "DESC"
    return f"{column} {direction}"


def build_lancamentos_count_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
    search: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    where_clause, params = build_lancamentos_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        search=search,
        exclude_mp_products=exclude_mp_products,
    )
    query = f"""
SELECT COUNT(*) AS total_items
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE {where_clause}
""".strip()
    return query, params


def build_lancamentos_data_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
    search: str | None = None,
    exclude_mp_products: bool = False,
    sort_by: str,
    sort_dir: str,
    page: int,
    page_size: int,
) -> tuple[str, tuple]:
    where_clause, params = build_lancamentos_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        search=search,
        exclude_mp_products=exclude_mp_products,
    )
    order_by = resolve_lancamentos_order_by(sort_by=sort_by, sort_dir=sort_dir)
    safe_page = max(int(page), 1)
    safe_page_size = min(max(int(page_size), 1), MAX_PAGE_SIZE)
    offset = (safe_page - 1) * safe_page_size
    query = f"""
SELECT
    {LANCAMENTOS_SELECT}
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE {where_clause}
ORDER BY {order_by}
OFFSET ? ROWS FETCH NEXT ? ROWS ONLY
""".strip()
    return query, params + (offset, safe_page_size)


def build_period_where(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    return build_query_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        exclude_mp_products=exclude_mp_products,
    )


def build_filiais_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
) -> tuple[str, tuple]:
    where_clause, params = build_period_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
    )
    query = f"""
SELECT DISTINCT
    LTRIM(RTRIM(filial)) AS codigo
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE {where_clause}
  AND LTRIM(RTRIM(filial)) <> ''
ORDER BY codigo
""".strip()
    return query, params


def build_centros_custo_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    where_clause, params = build_period_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        exclude_mp_products=exclude_mp_products,
    )
    query = f"""
SELECT DISTINCT
    LTRIM(RTRIM(centro_custo_codigo)) AS codigo,
    LTRIM(RTRIM(centro_custo_descricao)) AS descricao
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE {where_clause}
  AND LTRIM(RTRIM(centro_custo_codigo)) <> ''
ORDER BY codigo, descricao
""".strip()
    return query, params


def build_centros_custo_catalog_by_branch_query(*, branch: str) -> tuple[str, tuple]:
    """Catálogo somente leitura de CCs por filial (sem filtro de período).

    Reutiliza a mesma view do plugin financeiro-centro-custo; não duplica fonte.
    """
    query = f"""
SELECT DISTINCT
    LTRIM(RTRIM(filial)) AS filial,
    LTRIM(RTRIM(centro_custo_codigo)) AS codigo,
    LTRIM(RTRIM(centro_custo_descricao)) AS descricao
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE LTRIM(RTRIM(filial)) = ?
  AND LTRIM(RTRIM(centro_custo_codigo)) <> ''
ORDER BY codigo, descricao
""".strip()
    return query, (branch,)


def build_fornecedores_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    where_clause, params = build_query_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        exclude_mp_products=exclude_mp_products,
    )
    query = f"""
SELECT DISTINCT TOP ({MAX_FORNECEDORES_FILTROS})
    LTRIM(RTRIM(fornecedor_cliente_codigo)) AS codigo,
    LTRIM(RTRIM(loja)) AS loja,
    LTRIM(RTRIM(razao_social)) AS razao_social
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE {where_clause}
  AND LTRIM(RTRIM(fornecedor_cliente_codigo)) <> ''
ORDER BY codigo, loja, razao_social
""".strip()
    return query, params


def build_resumo_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    where_clause, params = build_query_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        exclude_mp_products=exclude_mp_products,
    )
    query = f"""
SELECT
    COALESCE(SUM(CAST(valor_total AS DECIMAL(18, 2))), 0) AS total_periodo,
    COUNT(*) AS quantidade_lancamentos,
    COUNT(
        DISTINCT LTRIM(RTRIM(centro_custo_codigo))
    ) AS quantidade_centros_custo,
    COUNT(
        DISTINCT CONCAT(
            LTRIM(RTRIM(fornecedor_cliente_codigo)),
            '|',
            LTRIM(RTRIM(loja))
        )
    ) AS quantidade_fornecedores,
    COALESCE(MAX(CAST(valor_total AS DECIMAL(18, 2))), 0) AS maior_lancamento
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE {where_clause}
""".strip()
    return query, params


def build_serie_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    where_clause, params = build_query_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        exclude_mp_products=exclude_mp_products,
    )
    query = f"""
SELECT
    LEFT(LTRIM(RTRIM(data_emissao)), 6) AS ano_mes,
    COALESCE(SUM(CAST(valor_total AS DECIMAL(18, 2))), 0) AS valor_total,
    COUNT(*) AS quantidade_lancamentos
FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
WHERE {where_clause}
GROUP BY LEFT(LTRIM(RTRIM(data_emissao)), 6)
ORDER BY ano_mes ASC
""".strip()
    return query, params


def build_ranking_centros_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    supplier_code: str | None = None,
    supplier_store: str | None = None,
    limit: int = DEFAULT_RANKING_LIMIT,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    """Ranking de centros: um GROUP BY na view + percentual via window.

    Evita CTE `scoped` materializada + `period_total` + segundo scan em `grouped`
    (padrão antigo relia a view três vezes no período cheio).
    """
    where_clause, params = build_query_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        supplier_code=supplier_code,
        supplier_store=supplier_store,
        exclude_mp_products=exclude_mp_products,
    )
    safe_limit = min(max(int(limit), 1), MAX_RANKING_LIMIT)
    query = f"""
WITH grouped AS (
    SELECT
        LTRIM(RTRIM(centro_custo_codigo)) AS centro_custo_codigo,
        MAX(LTRIM(RTRIM(centro_custo_descricao))) AS centro_custo_descricao,
        SUM(CAST(valor_total AS DECIMAL(18, 2))) AS valor_total,
        COUNT(*) AS quantidade_lancamentos
    FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
    WHERE {where_clause}
      AND LTRIM(RTRIM(centro_custo_codigo)) <> ''
    GROUP BY LTRIM(RTRIM(centro_custo_codigo))
)
SELECT TOP ({safe_limit})
    centro_custo_codigo,
    centro_custo_descricao,
    valor_total,
    quantidade_lancamentos,
    CASE
        WHEN SUM(valor_total) OVER () > 0
        THEN ROUND(valor_total * 100.0 / SUM(valor_total) OVER (), 2)
        ELSE 0
    END AS percentual
FROM grouped
ORDER BY valor_total DESC, centro_custo_codigo ASC
""".strip()
    return query, params


def build_ranking_fornecedores_query(
    *,
    start_date: str,
    end_date: str,
    branch: str | None = None,
    cost_center: str | None = None,
    limit: int = DEFAULT_RANKING_LIMIT,
    exclude_mp_products: bool = False,
) -> tuple[str, tuple]:
    """Ranking de fornecedores: mesmo padrão single-pass do ranking de centros."""
    where_clause, params = build_query_where(
        start_date=start_date,
        end_date=end_date,
        branch=branch,
        cost_center=cost_center,
        exclude_mp_products=exclude_mp_products,
    )
    safe_limit = min(max(int(limit), 1), MAX_RANKING_LIMIT)
    query = f"""
WITH grouped AS (
    SELECT
        LTRIM(RTRIM(fornecedor_cliente_codigo)) AS fornecedor_cliente_codigo,
        LTRIM(RTRIM(loja)) AS loja,
        MAX(LTRIM(RTRIM(razao_social))) AS razao_social,
        SUM(CAST(valor_total AS DECIMAL(18, 2))) AS valor_total,
        COUNT(*) AS quantidade_lancamentos
    FROM {DESPESAS_CENTRO_CUSTO_VIEW} WITH (NOLOCK)
    WHERE {where_clause}
      AND LTRIM(RTRIM(fornecedor_cliente_codigo)) <> ''
    GROUP BY
        LTRIM(RTRIM(fornecedor_cliente_codigo)),
        LTRIM(RTRIM(loja))
)
SELECT TOP ({safe_limit})
    fornecedor_cliente_codigo,
    loja,
    razao_social,
    valor_total,
    quantidade_lancamentos,
    CASE
        WHEN SUM(valor_total) OVER () > 0
        THEN ROUND(valor_total * 100.0 / SUM(valor_total) OVER (), 2)
        ELSE 0
    END AS percentual
FROM grouped
ORDER BY valor_total DESC, fornecedor_cliente_codigo ASC, loja ASC
""".strip()
    return query, params
