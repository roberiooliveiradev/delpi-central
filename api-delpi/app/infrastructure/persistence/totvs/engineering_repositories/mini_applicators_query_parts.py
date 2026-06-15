"""Fragmentos SQL reutilizáveis — mini-aplicadores (ferramentas)."""


def codigo_prefix_pattern(term: str) -> str:
    return f"{term.strip()}%"


def codigo_filter_sql() -> str:
    """Busca pelo início do código exibido (B1_COD ou grupo + '-' + B1_COD)."""
    return (
        "(RTRIM(LTRIM(SB1.B1_COD)) LIKE ? "
        "OR RTRIM(LTRIM(SB1.B1_GRUPO)) + '-' + RTRIM(LTRIM(SB1.B1_COD)) LIKE ?)"
    )
