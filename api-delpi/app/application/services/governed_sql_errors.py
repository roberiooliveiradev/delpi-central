# app/application/services/governed_sql_errors.py
"""Taxonomia de erros do caminho Governed Analytical SQL READ (S1).

Categorias internas bounded — nunca vazam connection string, host,
credenciais, stack ou diagnósticos brutos do SQL Server.
"""

SQL_VALIDATION_FAILED = "SQL_VALIDATION_FAILED"
OBJECT_NOT_ALLOWED = "OBJECT_NOT_ALLOWED"
COLUMN_NOT_ALLOWED = "COLUMN_NOT_ALLOWED"
QUERY_TOO_COMPLEX = "QUERY_TOO_COMPLEX"
QUERY_TIMEOUT = "QUERY_TIMEOUT"
RESULT_TOO_LARGE = "RESULT_TOO_LARGE"
SQL_SYNTAX_ERROR = "SQL_SYNTAX_ERROR"
POLICY_UNAVAILABLE = "POLICY_UNAVAILABLE"
EXECUTION_FAILED = "EXECUTION_FAILED"


class GovernedSqlError(Exception):
    """Erro categorizado do executor governado.

    `message` é seguro para propagação; `detail` pode conter informação
    interna e NÃO deve ser retornado ao chamador/modelo.
    """

    def __init__(self, category: str, message: str, *, detail: str | None = None):
        super().__init__(message)
        self.category = category
        self.message = message
        self.detail = detail

    def to_safe_dict(self) -> dict:
        return {"error": self.category, "message": self.message}


def map_permission_error(exc: PermissionError) -> GovernedSqlError:
    """Mapeia rejeições do SqlValidator para categorias bounded."""
    text = str(exc)
    if "whitelist" in text or "não autorizada" in text:
        category = OBJECT_NOT_ALLOWED
    elif "limite" in text or "excede" in text:
        category = QUERY_TOO_COMPLEX
    elif "governed indisponível" in text:
        category = POLICY_UNAVAILABLE
    else:
        category = SQL_VALIDATION_FAILED
    return GovernedSqlError(category, text)


def map_execution_error(exc: Exception) -> GovernedSqlError:
    """Mapeia erros pyodbc/execução para categorias seguras.

    O diagnóstico bruto vai apenas para `detail` (interno); `message`
    permanece genérico.
    """
    raw = str(exc)
    lowered = raw.lower()
    if "timeout" in lowered or "hyt00" in lowered or "hyt01" in lowered:
        return GovernedSqlError(
            QUERY_TIMEOUT,
            "Tempo limite de execução da consulta excedido.",
            detail=raw[:500],
        )
    if "syntax" in lowered or "incorrect syntax" in lowered:
        return GovernedSqlError(
            SQL_SYNTAX_ERROR,
            "Erro de sintaxe na consulta.",
            detail=raw[:500],
        )
    return GovernedSqlError(
        EXECUTION_FAILED,
        "Falha na execução da consulta.",
        detail=raw[:500],
    )
