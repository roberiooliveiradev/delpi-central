"""Regra de negócio: validade da economia de um kaizen.

Um kaizen contabiliza ganhos financeiros por **1 ano a partir da data de
implantação**. A partir do aniversário de 1 ano ele deixa de contribuir para os
ganhos financeiros (permanece no histórico, mas não soma mais no run-rate).

Regra pura (sem I/O): consumida tanto pela consolidação de ganhos (Sheets/
dashboard) quanto pelo enriquecimento do cadastro (Postgres) para expor
`savings_valid_until` / `savings_active` ao MFE.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Optional

VALIDITY_YEARS = 1

_IMPLEMENTED_STATUS = "implantado"


def _add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        # 29/02 em ano não bissexto → usa 28/02.
        return value.replace(year=value.year + years, day=28)


def savings_anniversary(implemented: Optional[date]) -> Optional[date]:
    """Data do aniversário de validade (primeiro dia em que NÃO conta mais)."""
    if implemented is None:
        return None
    return _add_years(implemented, VALIDITY_YEARS)


def savings_valid_until(implemented: Optional[date]) -> Optional[date]:
    """Último dia em que o kaizen ainda contabiliza ganhos (aniversário - 1 dia)."""
    anniversary = savings_anniversary(implemented)
    if anniversary is None:
        return None
    return anniversary - timedelta(days=1)


def _is_implemented(status: Optional[str]) -> bool:
    if not status:
        return False
    normalized = (
        str(status)
        .strip()
        .lower()
        .replace("í", "i")
        .replace("ú", "u")
        .replace("ã", "a")
    )
    return normalized == _IMPLEMENTED_STATUS


def is_savings_active(
    implemented: Optional[date],
    *,
    status: Optional[str] = None,
    reference: Optional[date] = None,
) -> bool:
    """Se, na data de referência, o kaizen ainda contabiliza ganhos.

    - Sem data de implantação → não conta.
    - Se `status` for informado, precisa estar implantado.
    - Conta apenas dentro da janela [implantação, válido_até].
    """
    if implemented is None:
        return False
    if status is not None and not _is_implemented(status):
        return False
    valid_until = savings_valid_until(implemented)
    ref = reference or date.today()
    return implemented <= ref <= valid_until


def active_days_in_range(
    implemented: Optional[date],
    range_start: Optional[date],
    range_end: Optional[date],
    *,
    today: Optional[date] = None,
) -> int:
    """Dias em que o kaizen contabiliza ganhos dentro do intervalo, com a
    janela de validade de 1 ano aplicada (cap no `savings_valid_until`).

    Nunca conta dias futuros: o fim efetivo é limitado a ``today`` (padrão:
    data corrente). Assim um filtro de competência futura retorna ganho 0.
    """
    if implemented is None:
        return 0

    reference_today = today or date.today()
    start = range_start or implemented
    end = range_end or reference_today

    effective_start = max(implemented, start)
    valid_until = savings_valid_until(implemented)
    if valid_until is None:
        return 0
    # Cap simultâneo: fim do período pedido, validade de 1 ano e “hoje”
    # (não projeta ganho em datas futuras).
    effective_end = min(end, valid_until, reference_today)

    if effective_start > effective_end:
        return 0
    return (effective_end - effective_start).days + 1
