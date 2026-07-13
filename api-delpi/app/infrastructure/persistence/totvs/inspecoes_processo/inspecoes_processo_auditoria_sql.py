"""SQL da auditoria apontamento × inspeção de processo (consultas leves por etapa)."""

from __future__ import annotations

from app.domain.production.production_fabril_appointment_scope import (
    EFICIENCIA_FABRIL_VIEW,
    EXCLUDED_WORK_CENTERS,
    STATUS_REGISTRO_OK,
)

EFICIENCIA_VIEW = EFICIENCIA_FABRIL_VIEW
POR_ENSAIADOR_VIEW = "dbo.vw_minha_delpi_inspecoes_processo_por_ensaiador"


def _excluded_ct_sql(column: str = "EF.CENTRO_TRABALHO") -> str:
    clauses = [f"RTRIM({column}) <> '{ct}'" for ct in EXCLUDED_WORK_CENTERS]
    return " AND ".join(clauses)


_EXCLUDED_CT = _excluded_ct_sql()

# Params: branch, data
AUDITORIA_APONTAMENTOS_BASE_SQL = f"""
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
WHERE EF.FILIAL = ?
  AND EF.DATA_PRODUCAO = ?
  AND EF.STATUS_REGISTRO = '{STATUS_REGISTRO_OK}'
  AND RTRIM(ISNULL(EF.FILIAL, '')) <> ''
  AND RTRIM(ISNULL(EF.OP, '')) <> ''
  AND RTRIM(ISNULL(EF.OPERACAO, '')) <> ''
  AND {_EXCLUDED_CT}
"""

# Params: branch
AUDITORIA_ENSAIADOR_MAP_SQL = f"""
SELECT DISTINCT
    RTRIM(PE.Matricula_Ensaiador) AS Matricula_Ensaiador,
    UPPER(RTRIM(ISNULL(PE.Login_Ensaiador, ''))) AS Login_Ensaiador,
    UPPER(RTRIM(ISNULL(PE.Nome_Ensaiador, ''))) AS Nome_Ensaiador
FROM {POR_ENSAIADOR_VIEW} PE WITH (NOLOCK)
WHERE PE.Filial = ?
  AND RTRIM(ISNULL(PE.Matricula_Ensaiador, '')) <> ''
"""


def build_qpr_for_ops_sql(op_count: int) -> str:
    """Params: branch + one LIKE param per OP (prefix seekable)."""
    if op_count < 1:
        raise ValueError("op_count must be >= 1")
    likes = " OR ".join(["QPR.QPR_OP LIKE ?" for _ in range(op_count)])
    return f"""
SELECT DISTINCT
    RTRIM(QPR.QPR_OP) AS Ordem_Producao,
    RTRIM(QPR.QPR_OPERAC) AS Operacao,
    RTRIM(QPR.QPR_ENSR) AS Matricula_Ensaiador
FROM dbo.QPR010 QPR WITH (NOLOCK)
WHERE QPR.D_E_L_E_T_ = ''
  AND QPR.QPR_FILIAL = ?
  AND RTRIM(ISNULL(QPR.QPR_ENSR, '')) <> ''
  AND ({likes})
"""


# Mantém nomes usados pelos testes de sanidade (conteúdo emblemático).
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
