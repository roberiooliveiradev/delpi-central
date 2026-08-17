"""SQL de KPIs de inspeções de processo filtrados por Data_Medicao_Date.

As views pré-agregadas (resumo_filial, por_produto, …) não têm grão de data.
Com start_date/end_date a agregação sai de historico_tela (NOLOCK, filtro SARGable).
"""

from __future__ import annotations

from app.domain.totvs.protheus_branches import (
    branch_filter_sql,
    is_all_branches,
)

HISTORICO_TELA_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_historico_tela"

_FILTERED_SELECT = """
        Filial,
        Unidade,
        Ordem_Producao,
        Codigo_Produto,
        Descricao_Produto,
        Revisao_Produto,
        Roteiro,
        Operacao,
        Recurso,
        Ferramenta,
        Centro_Trabalho,
        Descricao_Operacao,
        Laboratorio,
        Codigo_Ensaio,
        Nome_Ensaio,
        Matricula_Ensaiador,
        Nome_Ensaiador,
        Resultado_Codigo,
        Data_Medicao_Date
"""

_RESULT_OP = """
        CASE
            WHEN SUM(CASE WHEN Resultado_Codigo = 'R' THEN 1 ELSE 0 END) > 0 THEN 'R'
            WHEN SUM(CASE WHEN Resultado_Codigo = 'T' THEN 1 ELSE 0 END) > 0 THEN 'T'
            ELSE 'A'
        END
"""

_RANKING_ORDER_BY = """
ORDER BY
    Qtde_Ensaios_Reprovados DESC,
    Qtde_OPs_Reprovadas DESC,
    Qtde_Ensaios DESC
"""

_POR_PRODUTO_EXTRA = """
        MAX(Unidade) AS Unidade,
        MAX(Descricao_Produto) AS Descricao_Produto,
        MAX(Revisao_Produto) AS Revisao_Produto,
"""

_POR_ENSAIADOR_EXTRA = """
        MAX(Unidade) AS Unidade,
        MAX(Nome_Ensaiador) AS Nome_Ensaiador,
        CAST(NULL AS VARCHAR(40)) AS Login_Ensaiador,
"""

_RANKING_ENSAIO_EXTRA = """
        MAX(Unidade) AS Unidade,
        MAX(Laboratorio) AS Laboratorio,
        MAX(Nome_Ensaio) AS Nome_Ensaio,
"""

_POR_OPERACAO_EXTRA = """
        MAX(Unidade) AS Unidade,
        MAX(Descricao_Produto) AS Descricao_Produto,
        MAX(Revisao_Produto) AS Revisao_Produto,
        MAX(Roteiro) AS Roteiro,
        MAX(Recurso) AS Recurso,
        MAX(Ferramenta) AS Ferramenta,
        MAX(Centro_Trabalho) AS Centro_Trabalho,
        MAX(Descricao_Operacao) AS Descricao_Operacao,
"""


def _where_branch(column: str, scope: str) -> tuple[str, list]:
    clause, params = branch_filter_sql(column, scope)
    if not clause:
        return "1=1", []
    return clause, params


def build_period_filter_clause(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, list]:
    branch_clause, params = _where_branch("Filial", branch)
    clauses = [branch_clause]
    if start_date:
        clauses.append("Data_Medicao_Date >= ?")
        params.append(start_date)
    if end_date:
        clauses.append("Data_Medicao_Date <= ?")
        params.append(end_date)
    return " AND ".join(clauses), params


def _filtered_cte_sql(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, list]:
    where_sql, params = build_period_filter_clause(
        branch,
        start_date=start_date,
        end_date=end_date,
    )
    cte = f"""
filtered AS (
    SELECT {_FILTERED_SELECT}
    FROM {HISTORICO_TELA_VIEW} WITH (NOLOCK)
    WHERE {where_sql}
)
"""
    return cte, params


def _join_keys_sql(alias_left: str, alias_right: str, columns: tuple[str, ...]) -> str:
    parts = [f"{alias_left}.Filial = {alias_right}.Filial"]
    parts.extend(
        f"{alias_left}.{column} = {alias_right}.{column}" for column in columns
    )
    return " AND ".join(parts)


def _count_cte(name: str, column: str, group_columns: tuple[str, ...]) -> str:
    keys = ("Filial", *group_columns)
    keys_sql = ", ".join(keys)
    inner_group = f"{keys_sql}, {column}"
    return f"""
{name} AS (
    SELECT {keys_sql}, COUNT(*) AS cnt
    FROM (
        SELECT {inner_group}
        FROM filtered
        GROUP BY {inner_group}
    ) AS uniq_{name}
    GROUP BY {keys_sql}
)
"""


def _percent_ops_aprovadas(ops_alias: str = "o") -> str:
    return (
        f"CASE WHEN ISNULL({ops_alias}.Qtde_OPs, 0) > 0 "
        f"THEN 100.0 * ISNULL({ops_alias}.Qtde_OPs_Aprovadas, 0) / {ops_alias}.Qtde_OPs "
        "ELSE 0 END"
    )


def _percent_ops_reprovadas(ops_alias: str = "o") -> str:
    return (
        f"CASE WHEN ISNULL({ops_alias}.Qtde_OPs, 0) > 0 "
        f"THEN 100.0 * ISNULL({ops_alias}.Qtde_OPs_Reprovadas, 0) / {ops_alias}.Qtde_OPs "
        "ELSE 0 END"
    )


def _percent_ensaios_aprovados() -> str:
    return (
        "CASE WHEN e.Qtde_Ensaios > 0 "
        "THEN 100.0 * e.Qtde_Ensaios_Aprovados / e.Qtde_Ensaios "
        "ELSE 0 END"
    )


def _percent_ensaios_reprovados() -> str:
    return (
        "CASE WHEN e.Qtde_Ensaios > 0 "
        "THEN 100.0 * e.Qtde_Ensaios_Reprovados / e.Qtde_Ensaios "
        "ELSE 0 END"
    )


def _resumo_per_branch_sql(filtered_cte: str) -> str:
    return f"""
WITH {filtered_cte},
op_results AS (
    SELECT
        Filial,
        Ordem_Producao,
        {_RESULT_OP} AS Resultado_OP
    FROM filtered
    GROUP BY Filial, Ordem_Producao
),
ensaio_agg AS (
    SELECT
        Filial,
        MAX(Unidade) AS Unidade,
        COUNT_BIG(*) AS Qtde_Ensaios,
        SUM(CASE WHEN Resultado_Codigo = 'A' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Aprovados,
        SUM(CASE WHEN Resultado_Codigo = 'R' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Reprovados,
        SUM(CASE WHEN Resultado_Codigo = 'T' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Tolerancia,
        MIN(Data_Medicao_Date) AS Primeira_Data_Medicao_Date,
        MAX(Data_Medicao_Date) AS Ultima_Data_Medicao_Date
    FROM filtered
    GROUP BY Filial
),
op_agg AS (
    SELECT
        Filial,
        COUNT(*) AS Qtde_OPs,
        SUM(CASE WHEN Resultado_OP = 'A' THEN 1 ELSE 0 END) AS Qtde_OPs_Aprovadas,
        SUM(CASE WHEN Resultado_OP = 'R' THEN 1 ELSE 0 END) AS Qtde_OPs_Reprovadas,
        SUM(CASE WHEN Resultado_OP = 'T' THEN 1 ELSE 0 END) AS Qtde_OPs_Tolerancia
    FROM op_results
    GROUP BY Filial
),
{_count_cte("product_agg", "Codigo_Produto", ())},
{_count_cte("operacao_agg", "Operacao", ())},
{_count_cte("ensaiador_agg", "Matricula_Ensaiador", ())}
SELECT
    e.Filial,
    e.Unidade,
    ISNULL(o.Qtde_OPs, 0) AS Qtde_OPs,
    e.Qtde_Ensaios,
    e.Qtde_Ensaios_Aprovados,
    e.Qtde_Ensaios_Reprovados,
    e.Qtde_Ensaios_Tolerancia,
    ISNULL(o.Qtde_OPs_Aprovadas, 0) AS Qtde_OPs_Aprovadas,
    ISNULL(o.Qtde_OPs_Reprovadas, 0) AS Qtde_OPs_Reprovadas,
    ISNULL(o.Qtde_OPs_Tolerancia, 0) AS Qtde_OPs_Tolerancia,
    CAST(0 AS INT) AS Qtde_OPs_Nao_Identificadas,
    ISNULL(p.cnt, 0) AS Qtde_Produtos,
    ISNULL(op.cnt, 0) AS Qtde_Operacoes,
    ISNULL(en.cnt, 0) AS Qtde_Ensaiadores,
    e.Primeira_Data_Medicao_Date,
    e.Ultima_Data_Medicao_Date,
    {_percent_ops_aprovadas()} AS Percentual_OPs_Aprovadas,
    {_percent_ops_reprovadas()} AS Percentual_OPs_Reprovadas,
    {_percent_ensaios_aprovados()} AS Percentual_Ensaios_Aprovados,
    {_percent_ensaios_reprovados()} AS Percentual_Ensaios_Reprovados
FROM ensaio_agg e
LEFT JOIN op_agg o ON o.Filial = e.Filial
LEFT JOIN product_agg p ON p.Filial = e.Filial
LEFT JOIN operacao_agg op ON op.Filial = e.Filial
LEFT JOIN ensaiador_agg en ON en.Filial = e.Filial
"""


def build_resumo_period_sql(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
) -> tuple[str, list]:
    filtered_cte, params = _filtered_cte_sql(
        branch,
        start_date=start_date,
        end_date=end_date,
    )
    per_branch = _resumo_per_branch_sql(filtered_cte)
    if not is_all_branches(branch):
        return per_branch, params

    sql = f"""
SELECT
    SUM(Qtde_OPs) AS Qtde_OPs,
    SUM(Qtde_Ensaios) AS Qtde_Ensaios,
    SUM(Qtde_Ensaios_Aprovados) AS Qtde_Ensaios_Aprovados,
    SUM(Qtde_Ensaios_Reprovados) AS Qtde_Ensaios_Reprovados,
    SUM(Qtde_Ensaios_Tolerancia) AS Qtde_Ensaios_Tolerancia,
    SUM(Qtde_OPs_Aprovadas) AS Qtde_OPs_Aprovadas,
    SUM(Qtde_OPs_Reprovadas) AS Qtde_OPs_Reprovadas,
    SUM(Qtde_OPs_Tolerancia) AS Qtde_OPs_Tolerancia,
    SUM(Qtde_OPs_Nao_Identificadas) AS Qtde_OPs_Nao_Identificadas,
    SUM(Qtde_Produtos) AS Qtde_Produtos,
    SUM(Qtde_Operacoes) AS Qtde_Operacoes,
    SUM(Qtde_Ensaiadores) AS Qtde_Ensaiadores,
    MIN(Primeira_Data_Medicao_Date) AS Primeira_Data_Medicao_Date,
    MAX(Ultima_Data_Medicao_Date) AS Ultima_Data_Medicao_Date,
    CASE
        WHEN SUM(Qtde_OPs) > 0
        THEN 100.0 * SUM(Qtde_OPs_Aprovadas) / SUM(Qtde_OPs)
        ELSE 0
    END AS Percentual_OPs_Aprovadas,
    CASE
        WHEN SUM(Qtde_OPs) > 0
        THEN 100.0 * SUM(Qtde_OPs_Reprovadas) / SUM(Qtde_OPs)
        ELSE 0
    END AS Percentual_OPs_Reprovadas,
    CASE
        WHEN SUM(Qtde_Ensaios) > 0
        THEN 100.0 * SUM(Qtde_Ensaios_Aprovados) / SUM(Qtde_Ensaios)
        ELSE 0
    END AS Percentual_Ensaios_Aprovados,
    CASE
        WHEN SUM(Qtde_Ensaios) > 0
        THEN 100.0 * SUM(Qtde_Ensaios_Reprovados) / SUM(Qtde_Ensaios)
        ELSE 0
    END AS Percentual_Ensaios_Reprovados
FROM (
{per_branch}
) AS per_branch
"""
    return sql, params


def _build_period_ranking_sql(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
    limit: int,
    group_columns: tuple[str, ...],
    extra_select: str,
    extra_outer_columns: str,
    count_specs: tuple[tuple[str, str], ...],
) -> tuple[str, list]:
    filtered_cte, params = _filtered_cte_sql(
        branch,
        start_date=start_date,
        end_date=end_date,
    )
    dim = ", ".join(group_columns)
    dim_prefix = f"{dim}," if dim else ""
    op_group = f"Filial, {dim}, Ordem_Producao" if dim else "Filial, Ordem_Producao"
    ensaio_group = f"Filial, {dim}" if dim else "Filial"
    group_select = "".join(f"        e.{column},\n" for column in group_columns)

    count_ctes = "".join(
        "," + _count_cte(name, column, group_columns) for name, column in count_specs
    )
    count_joins = ""
    count_selects = ""
    for name, _column in count_specs:
        alias = {
            "product_cnt": "pc",
            "operacao_cnt": "oc",
            "ensaiador_cnt": "ec",
            "ensaio_cnt": "sc",
        }[name]
        count_joins += (
            f"\nLEFT JOIN {name} {alias} ON {_join_keys_sql(alias, 'e', group_columns)}"
        )
        field = {
            "product_cnt": "Qtde_Produtos",
            "operacao_cnt": "Qtde_Operacoes",
            "ensaiador_cnt": "Qtde_Ensaiadores",
            "ensaio_cnt": "Qtde_Ensaios_Distintos",
        }[name]
        count_selects += f"    ISNULL({alias}.cnt, 0) AS {field},\n"

    sql = f"""
WITH {filtered_cte},
op_results AS (
    SELECT
        Filial,
        {dim_prefix}
        Ordem_Producao,
        {_RESULT_OP} AS Resultado_OP
    FROM filtered
    GROUP BY {op_group}
),
ensaio_agg AS (
    SELECT
        Filial,
        {dim_prefix}
        {extra_select}
        COUNT_BIG(*) AS Qtde_Ensaios,
        SUM(CASE WHEN Resultado_Codigo = 'A' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Aprovados,
        SUM(CASE WHEN Resultado_Codigo = 'R' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Reprovados,
        SUM(CASE WHEN Resultado_Codigo = 'T' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Tolerancia,
        MIN(Data_Medicao_Date) AS Primeira_Data_Medicao_Date,
        MAX(Data_Medicao_Date) AS Ultima_Data_Medicao_Date
    FROM filtered
    GROUP BY {ensaio_group}
),
op_agg AS (
    SELECT
        Filial,
        {dim_prefix}
        COUNT(*) AS Qtde_OPs,
        SUM(CASE WHEN Resultado_OP = 'A' THEN 1 ELSE 0 END) AS Qtde_OPs_Aprovadas,
        SUM(CASE WHEN Resultado_OP = 'R' THEN 1 ELSE 0 END) AS Qtde_OPs_Reprovadas,
        SUM(CASE WHEN Resultado_OP = 'T' THEN 1 ELSE 0 END) AS Qtde_OPs_Tolerancia
    FROM op_results
    GROUP BY {ensaio_group}
){count_ctes}
SELECT
    e.Filial,
{group_select}{extra_outer_columns}
    ISNULL(o.Qtde_OPs, 0) AS Qtde_OPs,
    e.Qtde_Ensaios,
    e.Qtde_Ensaios_Aprovados,
    e.Qtde_Ensaios_Reprovados,
    e.Qtde_Ensaios_Tolerancia,
    ISNULL(o.Qtde_OPs_Aprovadas, 0) AS Qtde_OPs_Aprovadas,
    ISNULL(o.Qtde_OPs_Reprovadas, 0) AS Qtde_OPs_Reprovadas,
    ISNULL(o.Qtde_OPs_Tolerancia, 0) AS Qtde_OPs_Tolerancia,
{count_selects}    e.Primeira_Data_Medicao_Date,
    e.Ultima_Data_Medicao_Date,
    {_percent_ops_aprovadas()} AS Percentual_OPs_Aprovadas,
    {_percent_ops_reprovadas()} AS Percentual_OPs_Reprovadas,
    {_percent_ensaios_aprovados()} AS Percentual_Ensaios_Aprovados,
    {_percent_ensaios_reprovados()} AS Percentual_Ensaios_Reprovados
FROM ensaio_agg e
LEFT JOIN op_agg o ON {_join_keys_sql("o", "e", group_columns)}{count_joins}
{_RANKING_ORDER_BY}
OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
"""
    params.append(limit)
    return sql, params


def build_por_produto_period_sql(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
    limit: int,
) -> tuple[str, list]:
    return _build_period_ranking_sql(
        branch,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        group_columns=("Codigo_Produto",),
        extra_select=_POR_PRODUTO_EXTRA,
        extra_outer_columns="""    e.Unidade,
    e.Descricao_Produto,
    e.Revisao_Produto,
""",
        count_specs=(
            ("ensaio_cnt", "Codigo_Ensaio"),
            ("operacao_cnt", "Operacao"),
            ("ensaiador_cnt", "Matricula_Ensaiador"),
        ),
    )


def build_por_ensaiador_period_sql(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
    limit: int,
) -> tuple[str, list]:
    return _build_period_ranking_sql(
        branch,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        group_columns=("Matricula_Ensaiador",),
        extra_select=_POR_ENSAIADOR_EXTRA,
        extra_outer_columns="""    e.Unidade,
    e.Nome_Ensaiador,
    e.Login_Ensaiador,
""",
        count_specs=(
            ("product_cnt", "Codigo_Produto"),
            ("operacao_cnt", "Operacao"),
            ("ensaio_cnt", "Codigo_Ensaio"),
        ),
    )


def build_ranking_ensaio_period_sql(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
    limit: int,
) -> tuple[str, list]:
    return _build_period_ranking_sql(
        branch,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        group_columns=("Codigo_Ensaio",),
        extra_select=_RANKING_ENSAIO_EXTRA,
        extra_outer_columns="""    e.Unidade,
    e.Laboratorio,
    e.Nome_Ensaio,
""",
        count_specs=(
            ("product_cnt", "Codigo_Produto"),
            ("operacao_cnt", "Operacao"),
            ("ensaiador_cnt", "Matricula_Ensaiador"),
        ),
    )


def build_por_operacao_period_sql(
    branch: str,
    *,
    start_date: str | None,
    end_date: str | None,
    limit: int,
) -> tuple[str, list]:
    return _build_period_ranking_sql(
        branch,
        start_date=start_date,
        end_date=end_date,
        limit=limit,
        group_columns=("Codigo_Produto", "Operacao"),
        extra_select=_POR_OPERACAO_EXTRA,
        extra_outer_columns="""    e.Unidade,
    e.Descricao_Produto,
    e.Revisao_Produto,
    e.Roteiro,
    e.Recurso,
    e.Ferramenta,
    e.Centro_Trabalho,
    e.Descricao_Operacao,
""",
        count_specs=(
            ("ensaio_cnt", "Codigo_Ensaio"),
            ("ensaiador_cnt", "Matricula_Ensaiador"),
        ),
    )
