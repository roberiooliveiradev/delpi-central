from datetime import date

import pytest

from app.domain.services.kaizen.kaizen_indicator_eligibility import (
    counts_for_quantity,
    date_in_range,
    is_implemented_status,
    quantity_anchor_date,
)
from app.domain.services.kaizen.kaizen_status_date_rules import (
    KaizenStatusDateError,
    validate_status_dates,
)


def test_counts_for_quantity_includes_aprovado_and_implantado() -> None:
    assert counts_for_quantity("aprovado") is True
    assert counts_for_quantity("implantado") is True
    assert counts_for_quantity("recebido") is False
    assert counts_for_quantity("cancelado") is False


def test_is_implemented_status_only_implantado() -> None:
    assert is_implemented_status("implantado") is True
    assert is_implemented_status("aprovado") is False


def test_quantity_anchor_prefers_committee_date() -> None:
    assert quantity_anchor_date(date(2026, 3, 10), date(2026, 6, 1)) == date(2026, 3, 10)
    assert quantity_anchor_date(None, date(2026, 6, 1)) == date(2026, 6, 1)
    assert quantity_anchor_date(None, None) is None


def test_date_in_range() -> None:
    assert date_in_range(date(2026, 3, 15), date(2026, 3, 1), date(2026, 3, 31)) is True
    assert date_in_range(date(2026, 4, 1), date(2026, 3, 1), date(2026, 3, 31)) is False
    assert date_in_range(None, date(2026, 3, 1), date(2026, 3, 31)) is False


def test_validate_status_dates_aprovado_requires_committee() -> None:
    with pytest.raises(KaizenStatusDateError, match="aprovação no comitê"):
        validate_status_dates(status="aprovado", date_committee_approved=None)


def test_validate_status_dates_implantado_requires_implemented() -> None:
    with pytest.raises(KaizenStatusDateError, match="data de implantação"):
        validate_status_dates(status="implantado", date_implemented="")


def test_validate_status_dates_ok() -> None:
    validate_status_dates(
        status="aprovado",
        date_committee_approved="2026-03-10",
    )
    validate_status_dates(
        status="implantado",
        date_implemented="2026-06-01",
    )
    validate_status_dates(status="recebido")
