"""Bloqueio de inventário em SB2 (B2_DTINV / B2_DINVFIM).

No Protheus o saldo físico/financeiro (SB2) registra o período em que o
material está bloqueado para inventário no armazém. Sem data inicial não há
bloqueio; data final vazia significa bloqueio aberto a partir da inicial.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Any


def normalize_protheus_date(value: Any) -> str | None:
    """Normaliza data Protheus/ISO para ``YYYYMMDD``. Vazio / lixo → ``None``."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.date().strftime("%Y%m%d")
    if isinstance(value, date):
        return value.strftime("%Y%m%d")

    raw = str(value).strip()
    if not raw or set(raw) <= {"0"}:
        return None
    digits = "".join(ch for ch in raw if ch.isdigit())
    if len(digits) >= 8:
        candidate = digits[:8]
        try:
            datetime.strptime(candidate, "%Y%m%d")
        except ValueError:
            return None
        return candidate
    if len(raw) >= 10 and raw[4] == "-" and raw[7] == "-":
        try:
            parsed = datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None
        return parsed.strftime("%Y%m%d")
    return None


def is_inventory_blocked(
    *,
    block_start: Any,
    block_end: Any = None,
    as_of: date | None = None,
) -> bool:
    """True quando ``as_of`` cai no intervalo de inventário do SB2.

    Regra:
    - sem ``B2_DTINV`` → livre;
    - com início e sem fim → bloqueado a partir do início;
    - com início e fim → bloqueado se início ≤ as_of ≤ fim.
    """
    start = normalize_protheus_date(block_start)
    if start is None:
        return False
    day = (as_of or date.today()).strftime("%Y%m%d")
    if day < start:
        return False
    end = normalize_protheus_date(block_end)
    if end is None:
        return True
    return day <= end
