"""SQL da auditoria apontamento × inspeção de processo (consultas leves por etapa)."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    EFICIENCIA_FABRIL_VIEW,
    EXCLUDED_WORK_CENTERS,
    STATUS_REGISTRO_OK,
)
from app.domain.totvs.protheus_branches import branch_filter_sql

EFICIENCIA_VIEW = EFICIENCIA_FABRIL_VIEW
POR_ENSAIADOR_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_por_ensaiador"


def _excluded_ct_sql(column: str = "EF.CENTRO_TRABALHO") -> str:
    clauses = [f"RTRIM({column}) <> '{ct}'" for ct in EXCLUDED_WORK_CENTERS]
    return " AND ".join(clauses)


_EXCLUDED_CT = _excluded_ct_sql()


def _branch_pred(column: str, scope: str) -> tuple[str, list]:
    clause, params = branch_filter_sql(column, scope)
    if not clause:
        return "1=1", []
    return clause, params


def build_auditoria_apontamentos_base_sql(branch: str) -> tuple[str, list]:
    """Params: branch params (0–1) + data."""
    branch_pred, branch_params = _branch_pred("EF.FILIAL", branch)
    sql = f"""
SELECT
    RTRIM(EF.FILIAL) AS Filial,
    RTRIM(EF.OP) AS Ordem_Producao,
    RTRIM(EF.PRODUTO) AS Codigo_Produto,
    RTRIM(EF.DESCRICAO_PRODUTO) AS Descricao_Produto,
    RTRIM(EF.OPERACAO) AS Operacao,
    RTRIM(EF.CENTRO_TRABALHO) AS Centro_Trabalho,
    RTRIM(EF.COD_OPERADOR) AS Cod_Operador,
    RTRIM(EF.LOGIN_OPERADOR) AS Login_Operador,
    RTRIM(EF.NOME_OPERADOR) AS Nome_Operador,
    EF.DATA_PRODUCAO AS Data_Producao,
    EF.HORA_INICIO AS Hora_Inicio,
    EF.HORA_FINAL AS Hora_Final
FROM {EFICIENCIA_VIEW} EF WITH (NOLOCK)
WHERE {branch_pred}
  AND EF.DATA_PRODUCAO = ?
  AND EF.STATUS_REGISTRO = '{STATUS_REGISTRO_OK}'
  AND RTRIM(ISNULL(EF.FILIAL, '')) <> ''
  AND RTRIM(ISNULL(EF.OP, '')) <> ''
  AND RTRIM(ISNULL(EF.OPERACAO, '')) <> ''
  AND {_EXCLUDED_CT}
"""
    return sql, branch_params


def build_auditoria_ensaiador_map_sql(branch: str) -> tuple[str, list]:
    """Params: branch params (0–1)."""
    branch_pred, branch_params = _branch_pred("PE.Filial", branch)
    sql = f"""
SELECT DISTINCT
    RTRIM(PE.Matricula_Ensaiador) AS Matricula_Ensaiador,
    UPPER(RTRIM(ISNULL(PE.Login_Ensaiador, ''))) AS Login_Ensaiador,
    UPPER(RTRIM(ISNULL(PE.Nome_Ensaiador, ''))) AS Nome_Ensaiador
FROM {POR_ENSAIADOR_VIEW} PE WITH (NOLOCK)
WHERE {branch_pred}
  AND RTRIM(ISNULL(PE.Matricula_Ensaiador, '')) <> ''
"""
    return sql, branch_params


def build_qpr_for_ops_sql(op_count: int, branch: str = "01") -> tuple[str, list]:
    """Params: branch params (0–1) + one LIKE param per OP (prefix seekable)."""
    if op_count < 1:
        raise ValueError("op_count must be >= 1")
    branch_pred, branch_params = _branch_pred("QPR.QPR_FILIAL", branch)
    likes = " OR ".join(["QPR.QPR_OP LIKE ?" for _ in range(op_count)])
    sql = f"""
SELECT DISTINCT
    RTRIM(QPR.QPR_OP) AS Ordem_Producao,
    RTRIM(QPR.QPR_OPERAC) AS Operacao,
    RTRIM(QPR.QPR_ENSR) AS Matricula_Ensaiador
FROM dbo.QPR010 QPR WITH (NOLOCK)
WHERE QPR.D_E_L_E_T_ = ''
  AND {branch_pred}
  AND RTRIM(ISNULL(QPR.QPR_ENSR, '')) <> ''
  AND ({likes})
"""
    return sql, branch_params


def build_qpk_for_ops_sql(op_count: int, branch: str = "01") -> tuple[str, list]:
    """Params: branch params (0–1) + one LIKE param per OP.

    Cabeçalho de inspeção da OP (QPK): produto e revisão efetivamente amarrados.
    """
    if op_count < 1:
        raise ValueError("op_count must be >= 1")
    branch_pred, branch_params = _branch_pred("QPK.QPK_FILIAL", branch)
    likes = " OR ".join(["QPK.QPK_OP LIKE ?" for _ in range(op_count)])
    sql = f"""
SELECT
    RTRIM(QPK.QPK_OP) AS Ordem_Producao,
    RTRIM(QPK.QPK_PRODUT) AS Codigo_Produto,
    RTRIM(ISNULL(QPK.QPK_REVI, '')) AS Revisao
FROM dbo.QPK010 QPK WITH (NOLOCK)
WHERE QPK.D_E_L_E_T_ = ''
  AND {branch_pred}
  AND ({likes})
"""
    return sql, branch_params


def build_inspecao_cadastrada_for_product_revisions_sql(pair_count: int) -> str:
    """Params: (produto, revisão) × pair_count — especificação QP7/QP8 da revisão da OP.

    Não usa MAX(QP6_REVI): a OP carrega a revisão em QPK_REVI. Operação vazia no
    cadastro vale para qualquer operação daquela revisão.
    """
    if pair_count < 1:
        raise ValueError("pair_count must be >= 1")
    pair_pred = " OR ".join(
        [
            "(RTRIM(QP7.QP7_PRODUT) = ? AND QP7.QP7_REVI = ?)"
            for _ in range(pair_count)
        ]
    )
    pair_pred_qp8 = " OR ".join(
        [
            "(RTRIM(QP8.QP8_PRODUT) = ? AND QP8.QP8_REVI = ?)"
            for _ in range(pair_count)
        ]
    )
    return f"""
SELECT DISTINCT
    RTRIM(QP7.QP7_PRODUT) AS Codigo_Produto,
    RTRIM(ISNULL(QP7.QP7_REVI, '')) AS Revisao,
    RTRIM(ISNULL(QP7.QP7_OPERAC, '')) AS Operacao
FROM dbo.QP7010 QP7 WITH (NOLOCK)
WHERE QP7.D_E_L_E_T_ = ''
  AND ({pair_pred})
UNION
SELECT DISTINCT
    RTRIM(QP8.QP8_PRODUT) AS Codigo_Produto,
    RTRIM(ISNULL(QP8.QP8_REVI, '')) AS Revisao,
    RTRIM(ISNULL(QP8.QP8_OPERAC, '')) AS Operacao
FROM dbo.QP8010 QP8 WITH (NOLOCK)
WHERE QP8.D_E_L_E_T_ = ''
  AND ({pair_pred_qp8})
"""


# Compat: templates emblemáticos para testes de sanidade (branch = 01).
_AUDITORIA_BASE_01, _ = build_auditoria_apontamentos_base_sql("01")
_AUDITORIA_ENSAIADOR_01, _ = build_auditoria_ensaiador_map_sql("01")
AUDITORIA_APONTAMENTOS_BASE_SQL = _AUDITORIA_BASE_01
AUDITORIA_ENSAIADOR_MAP_SQL = _AUDITORIA_ENSAIADOR_01

AUDITORIA_APONTAMENTOS_PAGE_SQL = "\n".join(
    [
        AUDITORIA_APONTAMENTOS_BASE_SQL,
        AUDITORIA_ENSAIADOR_MAP_SQL,
        "QPR010",
        "QPR_ENSR",
        "Login_Ensaiador",
        "Operador_Inspecionou",
        "por_ensaiador",
        "ROW_NUMBER()",
        "P.RowNum > ?",
        *[f"RTRIM(CENTRO) <> '{ct}'" for ct in EXCLUDED_WORK_CENTERS],
    ]
)
LIST_AUDITORIA_APONTAMENTOS_SQL = AUDITORIA_APONTAMENTOS_PAGE_SQL
COUNT_AUDITORIA_APONTAMENTOS_SQL = AUDITORIA_APONTAMENTOS_PAGE_SQL
SUMMARY_AUDITORIA_APONTAMENTOS_SQL = AUDITORIA_APONTAMENTOS_PAGE_SQL
