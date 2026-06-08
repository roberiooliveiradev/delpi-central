"""Testes unitários do módulo de agendamento (helpers e regras de filial)."""

from __future__ import annotations

from datetime import datetime, timezone
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from app.application.security.api_delpi_permissions import CENTRAL_AGENDAMENTO_VIEW_FILIAL_ES
from app.interface.http.routes.scheduling.scheduling_router import (
    _branch_manage_allowed,
    _branch_view_allowed,
    _parse_iso_datetime,
)


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("2026-06-03T10:00:00+00:00", datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc)),
        ("2026-06-03T10:00:00Z", datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc)),
        ("invalid", None),
    ],
)
def test_parse_iso_datetime(value: str, expected: datetime | None) -> None:
    assert _parse_iso_datetime(value) == expected


def test_branch_view_allowed_with_view_permission() -> None:
    user = SimpleNamespace(
        is_superadmin=False,
        permissions=[CENTRAL_AGENDAMENTO_VIEW_FILIAL_ES],
    )

    with patch(
        "app.interface.http.routes.scheduling.scheduling_router.get_current_user",
        return_value=user,
    ):
        with patch(
            "app.interface.http.routes.scheduling.scheduling_router.has_permission",
            side_effect=lambda current_user, perm: perm in user.permissions,
        ):
            assert _branch_view_allowed("ES") is True
            assert _branch_view_allowed("SC") is False


def test_branch_manage_allowed_for_superadmin() -> None:
    user = SimpleNamespace(is_superadmin=True, permissions=[])

    with patch(
        "app.interface.http.routes.scheduling.scheduling_router.get_current_user",
        return_value=user,
    ):
        assert _branch_manage_allowed("ES") is True
        assert _branch_manage_allowed("SC") is True


def test_booking_time_ranges_overlap() -> None:
    """Espelha a condição SQL: start_a < end_b AND end_a > start_b."""

    def overlaps(start_a: datetime, end_a: datetime, start_b: datetime, end_b: datetime) -> bool:
        return start_a < end_b and end_a > start_b

    slot_a_start = datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc)
    slot_a_end = datetime(2026, 6, 3, 11, 0, tzinfo=timezone.utc)

    assert overlaps(
        datetime(2026, 6, 3, 10, 30, tzinfo=timezone.utc),
        datetime(2026, 6, 3, 11, 30, tzinfo=timezone.utc),
        slot_a_start,
        slot_a_end,
    )
    assert not overlaps(
        datetime(2026, 6, 3, 11, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 3, 12, 0, tzinfo=timezone.utc),
        slot_a_start,
        slot_a_end,
    )
    assert not overlaps(
        datetime(2026, 6, 3, 9, 0, tzinfo=timezone.utc),
        datetime(2026, 6, 3, 10, 0, tzinfo=timezone.utc),
        slot_a_start,
        slot_a_end,
    )
