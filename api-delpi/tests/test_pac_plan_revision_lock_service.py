from __future__ import annotations

import pytest

from app.domain.services.quality_action_plans.pac_plan_revision_lock_service import (
    REVISION_CONFLICT_MESSAGE,
    assert_expected_revision_number,
)


def test_assert_expected_revision_number_allows_match() -> None:
    assert_expected_revision_number(3, 3)


def test_assert_expected_revision_number_ignores_missing_expected() -> None:
    assert_expected_revision_number(3, None)


def test_assert_expected_revision_number_raises_on_mismatch() -> None:
    with pytest.raises(ValueError) as exc:
        assert_expected_revision_number(4, 3)
    assert exc.value.args[0] == REVISION_CONFLICT_MESSAGE
