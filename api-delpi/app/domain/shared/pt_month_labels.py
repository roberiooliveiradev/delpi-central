"""Abreviações de mês em pt-BR (sem depender de locale do SO / LC_TIME)."""

from __future__ import annotations

# Ordem jan–dez; minúsculas canônicas.
MONTH_ABBREV_PT: tuple[str, ...] = (
    "jan",
    "fev",
    "mar",
    "abr",
    "mai",
    "jun",
    "jul",
    "ago",
    "set",
    "out",
    "nov",
    "dez",
)


def month_abbrev_pt(month: int, *, capitalize: bool = True) -> str:
    """Retorna abreviação pt-BR do mês (1–12)."""
    if month < 1 or month > 12:
        raise ValueError(f"mês inválido: {month}")
    abbrev = MONTH_ABBREV_PT[month - 1]
    if not capitalize:
        return abbrev
    return f"{abbrev[:1].upper()}{abbrev[1:]}"


def format_month_year_chart_label(year: int, month: int) -> str:
    """Rótulo de série temporal mensal: «Jan. de 26»."""
    yy = str(year)[-2:].zfill(2)
    return f"{month_abbrev_pt(month)}. de {yy}"
