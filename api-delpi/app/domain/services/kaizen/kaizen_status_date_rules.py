"""Validação status × datas obrigatórias do kaizen.

- ``aprovado`` exige ``date_committee_approved``
- ``implantado`` exige ``date_implemented``
"""

from __future__ import annotations

from typing import Any, Optional


class KaizenStatusDateError(ValueError):
    """Regra de negócio: status avançado sem a data correspondente."""


def _has_date(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str) and not value.strip():
        return False
    return True


def _normalize_status(status: Optional[str]) -> str:
    if not status:
        return ""
    return str(status).strip().lower()


def validate_status_dates(
    *,
    status: Optional[str],
    date_committee_approved: Any = None,
    date_implemented: Any = None,
) -> None:
    """Levanta ``KaizenStatusDateError`` se o status exigir data ausente."""
    normalized = _normalize_status(status)
    if normalized == "aprovado" and not _has_date(date_committee_approved):
        raise KaizenStatusDateError(
            "Informe a data de aprovação no comitê para o status Aprovado."
        )
    if normalized == "implantado" and not _has_date(date_implemented):
        raise KaizenStatusDateError(
            "Informe a data de implantação para o status Implantado."
        )
