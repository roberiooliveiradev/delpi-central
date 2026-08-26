"""Convenções Delpi — usuário Protheus como operador de chão de fábrica.

Os apontamentos do PCP (``SH6.H6_OPERADO``, ``HZA.HZA_OPERAD``, ``SBC.BC_OPERADO``)
guardam o **usuário Protheus**, resolvido em ``SYS_USR`` por ``USR_ID``. O cadastro
de funcionários (``SRA010``) não cobre esses códigos na base Delpi.

Vínculo portal ↔ Protheus (Solicitações de Compras): ``USR_EMAIL`` em ``SYS_USR``,
comparado ao e-mail do usuário no core-api (aba TOTVS no Admin → Usuários).

Doc canônica: api-delpi/docs/api/padroes-totvs/apontamento-operacao-hza.md
"""

from __future__ import annotations

PROTHEUS_USER_TABLE = "SYS_USR"
PROTHEUS_USER_ID_COLUMN = "USR_ID"
PROTHEUS_USER_NAME_COLUMN = "USR_NOME"
PROTHEUS_USER_CODE_COLUMN = "USR_CODIGO"
PROTHEUS_USER_EMAIL_COLUMN = "USR_EMAIL"


def operator_name_join_sql(*, alias: str, operator_expr: str) -> str:
    """LEFT JOIN que resolve o nome do operador a partir do código apontado."""
    return (
        f"LEFT JOIN {PROTHEUS_USER_TABLE} {alias} WITH (NOLOCK)\n"
        f"    ON LTRIM(RTRIM({alias}.{PROTHEUS_USER_ID_COLUMN})) = {operator_expr}"
    )


def operator_name_expr(alias: str) -> str:
    return f"LTRIM(RTRIM(ISNULL({alias}.{PROTHEUS_USER_NAME_COLUMN}, '')))"
