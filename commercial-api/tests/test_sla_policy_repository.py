"""Unit tests for PostgresSlaPolicyRepository validation and mapping."""

from __future__ import annotations

import pytest

from commercial_app.infrastructure.persistence.repositories.postgres_sla_policy_repository import (
    PostgresSlaPolicyRepository,
    SlaPolicyConflictError,
    SlaPolicyValidationError,
)


def _repo() -> PostgresSlaPolicyRepository:
    return PostgresSlaPolicyRepository(connection=None)


def test_list_active_filters_and_maps_rows() -> None:
    repo = _repo()
    captured: dict[str, object] = {}

    def fake_fetch_all(query: str, params=None):  # noqa: ANN001
        captured["query"] = query
        captured["params"] = params
        return [
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "code": "OFFER-24H",
                "name": "Oferta 24h",
                "applies_to": "offer_stage",
                "duration_hours": 24,
                "calendar_code": None,
                "active": True,
                "created_at": None,
                "updated_at": None,
            }
        ]

    repo.fetch_all = fake_fetch_all  # type: ignore[method-assign]
    items = repo.list_active()
    assert "active = TRUE" in str(captured["query"])
    assert items == [
        {
            "id": "11111111-1111-1111-1111-111111111111",
            "code": "OFFER-24H",
            "name": "Oferta 24h",
            "appliesTo": "offer_stage",
            "durationHours": 24,
            "calendarCode": None,
            "active": True,
        }
    ]


def test_list_policies_include_inactive_omits_active_filter() -> None:
    repo = _repo()
    captured: dict[str, object] = {}

    def fake_fetch_all(query: str, params=None):  # noqa: ANN001
        captured["query"] = query
        return []

    repo.fetch_all = fake_fetch_all  # type: ignore[method-assign]
    assert repo.list_policies(include_inactive=True) == []
    assert "WHERE active = TRUE" not in str(captured["query"])


def test_create_validates_applies_to_and_hours() -> None:
    repo = _repo()
    with pytest.raises(SlaPolicyValidationError):
        repo.create(
            code="X",
            name="X",
            applies_to="invalid",
            duration_hours=8,
        )
    with pytest.raises(SlaPolicyValidationError):
        repo.create(
            code="X",
            name="X",
            applies_to="task",
            duration_hours=0,
        )


def test_create_rejects_duplicate_code() -> None:
    repo = _repo()
    repo.get_by_code = lambda code: {  # type: ignore[method-assign]
        "id": "11111111-1111-1111-1111-111111111111",
        "code": code,
        "name": "Existente",
        "appliesTo": "task",
        "durationHours": 8,
        "calendarCode": None,
        "active": True,
    }
    with pytest.raises(SlaPolicyConflictError):
        repo.create(
            code="TASK-8H",
            name="Tarefa",
            applies_to="task",
            duration_hours=8,
        )


def test_create_persists_and_returns_dict() -> None:
    repo = _repo()
    repo.get_by_code = lambda code: None  # type: ignore[method-assign]

    def fake_returning(query: str, params=None, **kwargs):  # noqa: ANN001
        assert "INSERT INTO commercial.sla_policies" in query
        assert params == ("TASK-8H", "Tarefa 8h", "task", 8, None, True)
        return {
            "id": "22222222-2222-2222-2222-222222222222",
            "code": "TASK-8H",
            "name": "Tarefa 8h",
            "applies_to": "task",
            "duration_hours": 8,
            "calendar_code": None,
            "active": True,
            "created_at": None,
            "updated_at": None,
        }

    repo.execute_returning_one = fake_returning  # type: ignore[method-assign]
    created = repo.create(
        code=" TASK-8H ",
        name=" Tarefa 8h ",
        applies_to="TASK",
        duration_hours=8,
    )
    assert created["code"] == "TASK-8H"
    assert created["appliesTo"] == "task"
    assert created["durationHours"] == 8
    assert created["active"] is True


def test_deactivate_sets_active_false() -> None:
    repo = _repo()
    calls: list[dict] = []

    def fake_get(policy_id: str):
        return {
            "id": "33333333-3333-3333-3333-333333333333",
            "code": "SAMPLE-48H",
            "name": "Amostra",
            "appliesTo": "sample",
            "durationHours": 48,
            "calendarCode": "BR",
            "active": True,
        }

    def fake_returning(query: str, params=None, **kwargs):  # noqa: ANN001
        calls.append({"query": query, "params": params})
        assert "UPDATE commercial.sla_policies" in query
        assert params[-2] is False  # active
        return {
            "id": "33333333-3333-3333-3333-333333333333",
            "code": "SAMPLE-48H",
            "name": "Amostra",
            "applies_to": "sample",
            "duration_hours": 48,
            "calendar_code": "BR",
            "active": False,
            "created_at": None,
            "updated_at": None,
        }

    repo.get_by_id = fake_get  # type: ignore[method-assign]
    repo.get_by_code = lambda code: None  # type: ignore[method-assign]
    repo.execute_returning_one = fake_returning  # type: ignore[method-assign]
    result = repo.deactivate("33333333-3333-3333-3333-333333333333")
    assert result is not None
    assert result["active"] is False
    assert calls
