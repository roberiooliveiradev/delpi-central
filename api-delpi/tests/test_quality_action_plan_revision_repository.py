from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from app.infrastructure.persistence.plugins.repositories.quality_action_plans.postgres_quality_action_plan_read_repository import (
    PostgresQualityActionPlanRepository,
)


@pytest.fixture
def repo() -> PostgresQualityActionPlanRepository:
    instance = PostgresQualityActionPlanRepository()
    instance._coerce_plan_id = MagicMock(return_value="11111111-1111-1111-1111-111111111111")
    return instance


def test_assert_expected_plan_revision_passes_when_numbers_match(repo) -> None:
    repo.fetch_one = MagicMock(return_value={"current_revision_number": 5})
    repo._assert_expected_plan_revision("plan-1", 5)
    repo.fetch_one.assert_called_once()


def test_assert_expected_plan_revision_raises_when_numbers_differ(repo) -> None:
    repo.fetch_one = MagicMock(return_value={"current_revision_number": 6})
    with pytest.raises(ValueError, match="Conflito de revisão"):
        repo._assert_expected_plan_revision("plan-1", 5)


def test_pop_expected_revision_removes_field_from_payload(repo) -> None:
    fields = {"title": "Novo título", "expected_revision_number": 2}
    assert repo._pop_expected_revision(fields) == 2
    assert fields == {"title": "Novo título"}
