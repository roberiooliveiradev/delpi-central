# app/tests/test_admin_statistics_repository.py

from unittest.mock import MagicMock

from app.infrastructure.persistence.sqlalchemy.admin_statistics_repository import (
    SqlAlchemyAdminStatisticsRepository,
)


def test_get_snapshot_returns_expected_sections():
    session = MagicMock()
    repo = SqlAlchemyAdminStatisticsRepository(session)
    repo._count = MagicMock(return_value=3)  # type: ignore[method-assign]
    repo._junction_count = MagicMock(return_value=1)  # type: ignore[method-assign]
    repo._count_users_without_roles = MagicMock(return_value=0)  # type: ignore[method-assign]
    repo._count_users_without_groups = MagicMock(return_value=0)  # type: ignore[method-assign]
    repo._roles_without_users = MagicMock(return_value=0)  # type: ignore[method-assign]
    repo._groups_without_users = MagicMock(return_value=0)  # type: ignore[method-assign]
    repo._apps_by_type = MagicMock(return_value=[{"type": "microfrontend", "count": 1}])  # type: ignore[method-assign]
    repo._top_roles_by_users = MagicMock(return_value=[])  # type: ignore[method-assign]
    repo._top_groups_by_users = MagicMock(return_value=[])  # type: ignore[method-assign]
    repo._top_groups_by_roles = MagicMock(return_value=[])  # type: ignore[method-assign]

    snapshot = repo.get_snapshot()

    assert "users" in snapshot
    assert "apps" in snapshot
    assert "roles" in snapshot
    assert "groups" in snapshot
    assert "permissions" in snapshot
    assert "assignments" in snapshot
    assert "notifications" in snapshot
    assert isinstance(snapshot["users"]["total"], int)
    assert isinstance(snapshot["apps"]["byType"], list)
    assert snapshot["apps"]["byType"][0]["type"] == "microfrontend"
