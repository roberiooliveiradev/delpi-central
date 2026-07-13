from __future__ import annotations

from app.domain.ports.inspecoes_processo.inspecoes_processo_repository_port import (
    InspecoesProcessoRepositoryPort,
)
from app.infrastructure.persistence.totvs.base_repository import BaseRepository
from app.infrastructure.persistence.totvs.inspecoes_processo.inspecoes_processo_auditoria_sql import (
    AUDITORIA_APONTAMENTOS_BASE_SQL,
    AUDITORIA_ENSAIADOR_MAP_SQL,
    build_qpr_for_ops_sql,
)

RESUMO_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_resumo_filial"
RANKING_ENSAIO_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_ranking_ensaio"
POR_PRODUTO_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_por_produto"
POR_OPERACAO_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_por_operacao"
POR_ENSAIADOR_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_por_ensaiador"
POR_OP_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_por_op"
HISTORICO_TELA_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_historico_tela"


def _as_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _aggregate_auditoria_apontamentos(rows: list[dict]) -> list[dict]:
    buckets: dict[tuple[str, str, str, str, str], dict] = {}
    for row in rows:
        key = (
            _as_text(row.get("Filial")),
            _as_text(row.get("Cod_Operador")),
            _as_text(row.get("Ordem_Producao")),
            _as_text(row.get("Codigo_Produto")),
            _as_text(row.get("Operacao")),
        )
        current = buckets.get(key)
        if current is None:
            buckets[key] = {
                "Filial": key[0],
                "Cod_Operador": key[1],
                "Login_Operador": _as_text(row.get("Login_Operador")),
                "Nome_Operador": _as_text(row.get("Nome_Operador")),
                "Ordem_Producao": key[2],
                "Codigo_Produto": key[3],
                "Descricao_Produto": _as_text(row.get("Descricao_Produto")),
                "Revisao_Produto": "",
                "Operacao": key[4],
                "Centro_Trabalho": _as_text(row.get("Centro_Trabalho")),
                "Data_Producao": row.get("Data_Producao"),
                "Hora_Inicio": row.get("Hora_Inicio"),
                "Hora_Final": row.get("Hora_Final"),
                "Qtde_Apontamentos": 1,
            }
            continue
        current["Qtde_Apontamentos"] = int(current["Qtde_Apontamentos"]) + 1
        if not current.get("Login_Operador"):
            current["Login_Operador"] = _as_text(row.get("Login_Operador"))
        if not current.get("Nome_Operador"):
            current["Nome_Operador"] = _as_text(row.get("Nome_Operador"))
        if not current.get("Descricao_Produto"):
            current["Descricao_Produto"] = _as_text(row.get("Descricao_Produto"))
        if not current.get("Centro_Trabalho"):
            current["Centro_Trabalho"] = _as_text(row.get("Centro_Trabalho"))
        hora_inicio = row.get("Hora_Inicio")
        hora_final = row.get("Hora_Final")
        if hora_inicio is not None and (
            current.get("Hora_Inicio") is None or str(hora_inicio) < str(current["Hora_Inicio"])
        ):
            current["Hora_Inicio"] = hora_inicio
        if hora_final is not None and (
            current.get("Hora_Final") is None or str(hora_final) > str(current["Hora_Final"])
        ):
            current["Hora_Final"] = hora_final
    return list(buckets.values())


def _index_ensaiador_map(rows: list[dict]) -> dict[str, dict[str, str]]:
    indexed: dict[str, dict[str, str]] = {}
    for row in rows:
        matricula = _as_text(row.get("Matricula_Ensaiador"))
        if not matricula:
            continue
        indexed[matricula] = {
            "login": _as_text(row.get("Login_Ensaiador")).upper(),
            "nome": _as_text(row.get("Nome_Ensaiador")).upper(),
        }
    return indexed


def _index_qpr_rows(rows: list[dict]) -> dict[tuple[str, str], set[str]]:
    indexed: dict[tuple[str, str], set[str]] = {}
    for row in rows:
        op = _as_text(row.get("Ordem_Producao"))
        operacao = _as_text(row.get("Operacao"))
        matricula = _as_text(row.get("Matricula_Ensaiador"))
        if not op or not operacao or not matricula:
            continue
        indexed.setdefault((op, operacao), set()).add(matricula)
    return indexed


def _mark_auditoria_rows(
    rows: list[dict],
    *,
    ensaiador_by_matricula: dict[str, dict[str, str]],
    qpr_by_op_oper: dict[tuple[str, str], set[str]],
) -> list[dict]:
    marked: list[dict] = []
    for row in rows:
        op = _as_text(row.get("Ordem_Producao"))
        operacao = _as_text(row.get("Operacao"))
        login = _as_text(row.get("Login_Operador")).upper()
        nome = _as_text(row.get("Nome_Operador")).upper()
        matriculas = qpr_by_op_oper.get((op, operacao), set())
        tem_inspecao = 1 if matriculas else 0
        operador_inspecionou = 0
        for matricula in matriculas:
            identity = ensaiador_by_matricula.get(matricula)
            if identity is None:
                continue
            if login and identity["login"] and identity["login"] == login:
                operador_inspecionou = 1
                break
            if nome and identity["nome"] and identity["nome"] == nome:
                operador_inspecionou = 1
                break
        marked.append(
            {
                **row,
                "Operador_Inspecionou": operador_inspecionou,
                "Tem_Inspecao_Na_Op_Operacao": tem_inspecao,
                "Tem_Inspecao_Executada": operador_inspecionou,
                "Tem_Inspecao_Amarrada": 0,
            }
        )
    return marked


def _summarize_auditoria_rows(rows: list[dict]) -> dict:
    pendentes = [row for row in rows if not row.get("Operador_Inspecionou")]
    operadores = {
        _as_text(row.get("Cod_Operador"))
        for row in pendentes
        if _as_text(row.get("Cod_Operador"))
    }
    ops_ops = {
        f"{_as_text(row.get('Ordem_Producao'))}|{_as_text(row.get('Operacao'))}"
        for row in pendentes
    }
    return {
        "Operadores_Pendentes": len(operadores),
        "Apontamentos_Pendentes": len(pendentes),
        "Ops_Operacoes_Pendentes": len(ops_ops),
        "Apontamentos_Com_Inspecao": len(rows) - len(pendentes),
        "Apontamentos_Total": len(rows),
    }


_RESUMO_SELECT = """
    Filial,
    Unidade,
    Qtde_OPs,
    Qtde_Ensaios,
    Qtde_Ensaios_Aprovados,
    Qtde_Ensaios_Reprovados,
    Qtde_Ensaios_Tolerancia,
    Qtde_OPs_Aprovadas,
    Qtde_OPs_Reprovadas,
    Qtde_OPs_Tolerancia,
    Qtde_OPs_Nao_Identificadas,
    Qtde_Produtos,
    Qtde_Operacoes,
    Qtde_Ensaiadores,
    Primeira_Data_Medicao_Date,
    Ultima_Data_Medicao_Date,
    Percentual_OPs_Aprovadas,
    Percentual_OPs_Reprovadas,
    Percentual_Ensaios_Aprovados,
    Percentual_Ensaios_Reprovados
"""

_RANKING_ENSAIO_SELECT = """
    Filial,
    Unidade,
    Laboratorio,
    Codigo_Ensaio,
    Nome_Ensaio,
    Qtde_OPs,
    Qtde_Ensaios,
    Qtde_Ensaios_Aprovados,
    Qtde_Ensaios_Reprovados,
    Qtde_Ensaios_Tolerancia,
    Qtde_OPs_Aprovadas,
    Qtde_OPs_Reprovadas,
    Qtde_Produtos,
    Qtde_Operacoes,
    Qtde_Ensaiadores,
    Primeira_Data_Medicao_Date,
    Ultima_Data_Medicao_Date,
    Percentual_OPs_Aprovadas,
    Percentual_OPs_Reprovadas,
    Percentual_Ensaios_Aprovados,
    Percentual_Ensaios_Reprovados
"""

_RANKING_ENSAIO_ORDER_BY = """
    ORDER BY
        Qtde_Ensaios_Reprovados DESC,
        Qtde_OPs_Reprovadas DESC,
        Qtde_Ensaios DESC
"""

_POR_PRODUTO_SELECT = """
    Filial,
    Unidade,
    Codigo_Produto,
    Descricao_Produto,
    Revisao_Produto,
    Qtde_OPs,
    Qtde_Ensaios,
    Qtde_Ensaios_Aprovados,
    Qtde_Ensaios_Reprovados,
    Qtde_Ensaios_Tolerancia,
    Qtde_OPs_Aprovadas,
    Qtde_OPs_Reprovadas,
    Qtde_OPs_Tolerancia,
    Qtde_Ensaios_Distintos,
    Qtde_Operacoes,
    Qtde_Ensaiadores,
    Primeira_Data_Medicao_Date,
    Ultima_Data_Medicao_Date,
    Percentual_OPs_Aprovadas,
    Percentual_OPs_Reprovadas,
    Percentual_Ensaios_Aprovados,
    Percentual_Ensaios_Reprovados
"""

_POR_PRODUTO_ORDER_BY = """
    ORDER BY
        Qtde_Ensaios_Reprovados DESC,
        Qtde_OPs_Reprovadas DESC,
        Qtde_Ensaios DESC
"""

_POR_OPERACAO_SELECT = """
    Filial,
    Unidade,
    Codigo_Produto,
    Descricao_Produto,
    Revisao_Produto,
    Roteiro,
    Operacao,
    Recurso,
    Ferramenta,
    Centro_Trabalho,
    Descricao_Operacao,
    Qtde_OPs,
    Qtde_Ensaios,
    Qtde_Ensaios_Aprovados,
    Qtde_Ensaios_Reprovados,
    Qtde_Ensaios_Tolerancia,
    Qtde_OPs_Aprovadas,
    Qtde_OPs_Reprovadas,
    Qtde_OPs_Tolerancia,
    Qtde_Ensaios_Distintos,
    Qtde_Ensaiadores,
    Primeira_Data_Medicao_Date,
    Ultima_Data_Medicao_Date,
    Percentual_OPs_Aprovadas,
    Percentual_OPs_Reprovadas,
    Percentual_Ensaios_Aprovados,
    Percentual_Ensaios_Reprovados
"""

_POR_OPERACAO_ORDER_BY = """
    ORDER BY
        Qtde_Ensaios_Reprovados DESC,
        Qtde_OPs_Reprovadas DESC,
        Qtde_Ensaios DESC
"""

_POR_ENSAIADOR_SELECT = """
    Filial,
    Unidade,
    Matricula_Ensaiador,
    Nome_Ensaiador,
    Login_Ensaiador,
    Qtde_OPs,
    Qtde_Ensaios,
    Qtde_Ensaios_Aprovados,
    Qtde_Ensaios_Reprovados,
    Qtde_Ensaios_Tolerancia,
    Qtde_OPs_Aprovadas,
    Qtde_OPs_Reprovadas,
    Qtde_Produtos,
    Qtde_Operacoes,
    Qtde_Ensaios_Distintos,
    Primeira_Data_Medicao_Date,
    Ultima_Data_Medicao_Date,
    Percentual_OPs_Aprovadas,
    Percentual_OPs_Reprovadas,
    Percentual_Ensaios_Aprovados,
    Percentual_Ensaios_Reprovados
"""

_POR_ENSAIADOR_ORDER_BY = """
    ORDER BY
        Qtde_Ensaios_Reprovados DESC,
        Qtde_OPs_Reprovadas DESC,
        Qtde_Ensaios DESC
"""

_HISTORICO_SELECT = """
    Filial,
    Unidade,
    Ordem_Producao,
    Codigo_Produto,
    Descricao_Produto,
    Revisao_Produto,
    Quantidade_OP,
    Chave_Cabecalho_Inspecao,
    Origem_Inspecao,
    Qtde_Ensaios,
    Qtde_Ensaios_Aprovados,
    Qtde_Ensaios_Reprovados,
    Qtde_Ensaios_Tolerancia,
    Qtde_Operacoes,
    Qtde_Ensaiadores,
    Resultado_Inspecao_Codigo,
    Resultado_Inspecao,
    Primeira_Data_Medicao_Date,
    Ultima_Data_Medicao_Date,
    Ultima_Hora_Medicao,
    Matricula_Ultimo_Ensaiador,
    Nome_Ultimo_Ensaiador
"""

_HISTORICO_ORDER_BY = """
    ORDER BY
        Ultima_Data_Medicao_Date DESC,
        Ordem_Producao DESC
"""

_HISTORICO_DETALHE_ITEM_SELECT = """
    Inspecao_Id,
    Ensaio_Id,
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
    Especificacao_Textual,
    Valor_Nominal,
    Limite_Inferior_Especificacao,
    Limite_Superior_Especificacao,
    Limite_Inferior_Controle,
    Limite_Superior_Controle,
    Regra_Min_Max,
    Unidade_Especificacao,
    Especificacao_Esperada,
    Medicao_Textual,
    Medicao_Numerica_A,
    Medicao_Numerica_N,
    Medicao_Numerica,
    Modo_Medicao_Numerica,
    Fonte_Medicao,
    Resultado_Codigo,
    Resultado,
    Data_Medicao_Date,
    Hora_Medicao,
    Matricula_Ensaiador,
    Nome_Ensaiador,
    Chave_Medicao,
    QPR_RECNO
"""

_HISTORICO_DETALHE_ITEM_ORDER_BY = """
    ORDER BY
        Operacao ASC,
        Codigo_Ensaio ASC,
        Data_Medicao_Date ASC,
        Hora_Medicao ASC,
        QPR_RECNO ASC
"""


def _normalize_exact_filter(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _build_historico_where(
    branch: str,
    *,
    ordem_producao: str | None = None,
    codigo_produto: str | None = None,
    resultado: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> tuple[str, list]:
    """Filtros SARGable: evita funções na coluna (UPPER/LTRIM/RTRIM) que impedem índice."""
    clauses = ["Filial = ?"]
    params: list = [branch]

    ordem = _normalize_exact_filter(ordem_producao)
    if ordem:
        # CHAR Protheus com espaços à direita: prefixo exact + % permanece seekable.
        clauses.append("Ordem_Producao LIKE ?")
        params.append(f"{ordem}%")

    produto = _normalize_exact_filter(codigo_produto)
    if produto:
        clauses.append("Codigo_Produto LIKE ?")
        params.append(f"{produto}%")

    resultado_norm = _normalize_exact_filter(resultado)
    if resultado_norm:
        clauses.append("Resultado_Inspecao_Codigo = ?")
        params.append(resultado_norm.upper())

    if data_inicio:
        clauses.append("Ultima_Data_Medicao_Date >= ?")
        params.append(data_inicio)
    if data_fim:
        clauses.append("Ultima_Data_Medicao_Date <= ?")
        params.append(data_fim)

    return " AND ".join(clauses), params


def _build_historico_list_filters(
    branch: str,
    *,
    ordem_producao: str | None = None,
    codigo_produto: str | None = None,
    data_inicio: str | None = None,
    data_fim: str | None = None,
) -> tuple[str, list]:
    """WHERE SARGable para listagem agregada em historico_tela.

    Datas filtradas em Data_Medicao_Date (antes do GROUP BY) — HAVING em
    MAX(Data_Medicao_Date) força scan da filial inteira e estoura timeout.
    """
    clauses = ["Filial = ?"]
    params: list = [branch]

    ordem = _normalize_exact_filter(ordem_producao)
    if ordem:
        clauses.append("Ordem_Producao LIKE ?")
        params.append(f"{ordem}%")

    produto = _normalize_exact_filter(codigo_produto)
    if produto:
        clauses.append("Codigo_Produto LIKE ?")
        params.append(f"{produto}%")

    if data_inicio:
        clauses.append("Data_Medicao_Date >= ?")
        params.append(data_inicio)
    if data_fim:
        clauses.append("Data_Medicao_Date <= ?")
        params.append(data_fim)

    return " AND ".join(clauses), params


_HISTORICO_TELA_LIST_SELECT = """
    Filial,
    MAX(Unidade) AS Unidade,
    Ordem_Producao,
    MAX(Codigo_Produto) AS Codigo_Produto,
    MAX(Descricao_Produto) AS Descricao_Produto,
    MAX(Revisao_Produto) AS Revisao_Produto,
    CAST(NULL AS FLOAT) AS Quantidade_OP,
    CAST('' AS VARCHAR(40)) AS Chave_Cabecalho_Inspecao,
    CAST('' AS VARCHAR(40)) AS Origem_Inspecao,
    COUNT_BIG(*) AS Qtde_Ensaios,
    SUM(CASE WHEN Resultado_Codigo = 'A' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Aprovados,
    SUM(CASE WHEN Resultado_Codigo = 'R' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Reprovados,
    SUM(CASE WHEN Resultado_Codigo = 'T' THEN 1 ELSE 0 END) AS Qtde_Ensaios_Tolerancia,
    CAST(0 AS INT) AS Qtde_Operacoes,
    CAST(0 AS INT) AS Qtde_Ensaiadores,
    CASE
        WHEN SUM(CASE WHEN Resultado_Codigo = 'R' THEN 1 ELSE 0 END) > 0 THEN 'R'
        WHEN SUM(CASE WHEN Resultado_Codigo = 'T' THEN 1 ELSE 0 END) > 0 THEN 'T'
        ELSE 'A'
    END AS Resultado_Inspecao_Codigo,
    CASE
        WHEN SUM(CASE WHEN Resultado_Codigo = 'R' THEN 1 ELSE 0 END) > 0 THEN 'REPROVADO'
        WHEN SUM(CASE WHEN Resultado_Codigo = 'T' THEN 1 ELSE 0 END) > 0 THEN 'TOLERANCIA'
        ELSE 'APROVADO'
    END AS Resultado_Inspecao,
    MIN(Data_Medicao_Date) AS Primeira_Data_Medicao_Date,
    MAX(Data_Medicao_Date) AS Ultima_Data_Medicao_Date,
    MAX(Hora_Medicao) AS Ultima_Hora_Medicao,
    MAX(Matricula_Ensaiador) AS Matricula_Ultimo_Ensaiador,
    MAX(Nome_Ensaiador) AS Nome_Ultimo_Ensaiador
"""


def _normalize_op_key(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


class InspecoesProcessoRepository(BaseRepository, InspecoesProcessoRepositoryPort):
    def get_resumo_by_branch(self, branch: str) -> dict | None:
        with self:
            return self.execute_one(
                f"""
                SELECT {_RESUMO_SELECT}
                FROM {RESUMO_VIEW}
                WHERE Filial = ?
                """,
                (branch,),
            )

    def list_ranking_ensaio_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]:
        with self:
            return self.execute_query(
                f"""
                SELECT {_RANKING_ENSAIO_SELECT}
                FROM {RANKING_ENSAIO_VIEW}
                WHERE Filial = ?
                {_RANKING_ENSAIO_ORDER_BY}
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                """,
                (branch, limit),
            )

    def list_por_produto_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]:
        with self:
            return self.execute_query(
                f"""
                SELECT {_POR_PRODUTO_SELECT}
                FROM {POR_PRODUTO_VIEW}
                WHERE Filial = ?
                {_POR_PRODUTO_ORDER_BY}
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                """,
                (branch, limit),
            )

    def list_por_operacao_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]:
        with self:
            return self.execute_query(
                f"""
                SELECT {_POR_OPERACAO_SELECT}
                FROM {POR_OPERACAO_VIEW}
                WHERE Filial = ?
                {_POR_OPERACAO_ORDER_BY}
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                """,
                (branch, limit),
            )

    def list_por_ensaiador_by_branch(
        self,
        branch: str,
        *,
        limit: int,
    ) -> list[dict]:
        with self:
            return self.execute_query(
                f"""
                SELECT {_POR_ENSAIADOR_SELECT}
                FROM {POR_ENSAIADOR_VIEW}
                WHERE Filial = ?
                {_POR_ENSAIADOR_ORDER_BY}
                OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY
                """,
                (branch, limit),
            )

    def list_historico_by_branch(
        self,
        branch: str,
        *,
        offset: int,
        fetch_next: int,
        ordem_producao: str | None = None,
        codigo_produto: str | None = None,
        resultado: str | None = None,
        data_inicio: str | None = None,
        data_fim: str | None = None,
    ) -> list[dict]:
        # Duas etapas leves em historico_tela: (1) TOP de OPs por data; (2) agregação
        # só dessas OPs. Evita ORDER BY global em por_op e COUNT(DISTINCT) caro.
        safe_offset = max(int(offset), 0)
        safe_fetch = max(int(fetch_next), 1)
        top_n = safe_offset + safe_fetch
        where_clause, params = _build_historico_list_filters(
            branch,
            ordem_producao=ordem_producao,
            codigo_produto=codigo_produto,
            data_inicio=data_inicio,
            data_fim=data_fim,
        )
        resultado_norm = _normalize_exact_filter(resultado)
        key_top = min(top_n * 8, 400) if resultado_norm else top_n

        with self:
            key_rows = self.execute_query(
                f"""
                SELECT TOP ({key_top}) Ordem_Producao
                FROM (
                    SELECT
                        Ordem_Producao,
                        MAX(Data_Medicao_Date) AS Ultima_Data_Medicao_Date
                    FROM {HISTORICO_TELA_VIEW} WITH (NOLOCK)
                    WHERE {where_clause}
                    GROUP BY Ordem_Producao
                ) AS op_keys
                ORDER BY
                    Ultima_Data_Medicao_Date DESC,
                    Ordem_Producao DESC
                """,
                tuple(params),
            )
            op_keys: list[str] = []
            seen: set[str] = set()
            for row in key_rows:
                op_key = _normalize_op_key(row.get("Ordem_Producao"))
                if not op_key or op_key in seen:
                    continue
                seen.add(op_key)
                op_keys.append(op_key)
            if not op_keys:
                return []

            op_predicates = " OR ".join(
                ["Ordem_Producao LIKE ?" for _ in op_keys]
            )
            enrich_params: list = [branch, *[f"{op_key}%" for op_key in op_keys]]
            rows = self.execute_query(
                f"""
                SELECT {_HISTORICO_TELA_LIST_SELECT}
                FROM {HISTORICO_TELA_VIEW} WITH (NOLOCK)
                WHERE Filial = ?
                  AND ({op_predicates})
                GROUP BY Filial, Ordem_Producao
                """,
                tuple(enrich_params),
            )

        by_op: dict[str, dict] = {}
        for row in rows:
            op_key = _normalize_op_key(row.get("Ordem_Producao"))
            if not op_key or op_key in by_op:
                continue
            if resultado_norm:
                codigo = _normalize_exact_filter(
                    str(row.get("Resultado_Inspecao_Codigo") or "")
                )
                if (codigo or "").upper() != resultado_norm.upper():
                    continue
            by_op[op_key] = row

        ordered = [by_op[op_key] for op_key in op_keys if op_key in by_op]
        return ordered[safe_offset : safe_offset + safe_fetch]

    def get_historico_cabecalho_by_op(
        self,
        branch: str,
        *,
        ordem_producao: str,
    ) -> dict | None:
        # por_op com filtro por OP também estoura timeout; cabeçalho agrega historico_tela.
        ordem = ordem_producao.strip()
        with self:
            return self.execute_one(
                f"""
                SELECT {_HISTORICO_TELA_LIST_SELECT}
                FROM {HISTORICO_TELA_VIEW} WITH (NOLOCK)
                WHERE Filial = ?
                  AND Ordem_Producao LIKE ?
                GROUP BY Filial, Ordem_Producao
                """,
                (branch, f"{ordem}%"),
            )

    def list_historico_detalhe_itens_by_op(
        self,
        branch: str,
        *,
        offset: int,
        fetch_next: int,
        ordem_producao: str,
    ) -> list[dict]:
        ordem = ordem_producao.strip()
        safe_offset = max(int(offset), 0)
        safe_fetch = max(int(fetch_next), 1)
        top_n = safe_offset + safe_fetch
        with self:
            rows = self.execute_query(
                f"""
                SELECT TOP ({top_n}) {_HISTORICO_DETALHE_ITEM_SELECT}
                FROM {HISTORICO_TELA_VIEW} WITH (NOLOCK)
                WHERE Filial = ?
                  AND Ordem_Producao LIKE ?
                {_HISTORICO_DETALHE_ITEM_ORDER_BY}
                """,
                (branch, f"{ordem}%"),
            )
        return rows[safe_offset:]

    def list_auditoria_apontamentos_page(
        self,
        branch: str,
        *,
        data: str,
        offset: int,
        fetch_next: int,
    ) -> tuple[dict, list[dict]]:
        safe_offset = max(int(offset), 0)
        safe_fetch = max(int(fetch_next), 1)
        empty_summary = {
            "Operadores_Pendentes": 0,
            "Apontamentos_Pendentes": 0,
            "Ops_Operacoes_Pendentes": 0,
            "Apontamentos_Com_Inspecao": 0,
            "Apontamentos_Total": 0,
        }

        with self:
            raw_rows = self.execute_query(
                AUDITORIA_APONTAMENTOS_BASE_SQL,
                (branch, data),
            )
            if not raw_rows:
                return empty_summary, []

            ensaiador_rows = self.execute_query(
                AUDITORIA_ENSAIADOR_MAP_SQL,
                (branch,),
            )

            ops = sorted(
                {
                    str(row.get("Ordem_Producao") or "").strip()
                    for row in raw_rows
                    if str(row.get("Ordem_Producao") or "").strip()
                }
            )
            qpr_rows: list[dict] = []
            if ops:
                # Lotear para não estourar limite de parâmetros do ODBC.
                chunk_size = 40
                for start in range(0, len(ops), chunk_size):
                    chunk = ops[start : start + chunk_size]
                    sql = build_qpr_for_ops_sql(len(chunk))
                    params = (branch, *[f"{op}%" for op in chunk])
                    qpr_rows.extend(self.execute_query(sql, params))

        aggregated = _aggregate_auditoria_apontamentos(raw_rows)
        ensaiador_by_matricula = _index_ensaiador_map(ensaiador_rows)
        qpr_by_op_oper = _index_qpr_rows(qpr_rows)
        marked = _mark_auditoria_rows(
            aggregated,
            ensaiador_by_matricula=ensaiador_by_matricula,
            qpr_by_op_oper=qpr_by_op_oper,
        )
        summary = _summarize_auditoria_rows(marked)
        marked.sort(
            key=lambda row: (
                0 if not row.get("Operador_Inspecionou") else 1,
                str(row.get("Nome_Operador") or ""),
                str(row.get("Cod_Operador") or ""),
                str(row.get("Ordem_Producao") or ""),
                str(row.get("Operacao") or ""),
            )
        )
        page = marked[safe_offset : safe_offset + safe_fetch]
        return summary, page
