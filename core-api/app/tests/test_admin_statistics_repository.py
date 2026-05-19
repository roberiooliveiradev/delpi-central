# app/tests/test_admin_statistics_repository.py

from app.create_app import create_app
from app.infrastructure.persistence.sqlalchemy.admin_statistics_repository import (
    SqlAlchemyAdminStatisticsRepository,
)
from app.extensions.db import db


def test_get_snapshot_returns_expected_sections():
    app = create_app("testing")

    with app.app_context():
        repo = SqlAlchemyAdminStatisticsRepository(db.session)
        snapshot = repo.get_snapshot()

    assert "users" in snapshot
    assert "apps" in snapshot
    assert "roles" in snapshot
    assert "groups" in snapshot
    assert "permissions" in snapshot
    assert "assignments" in snapshot
    assert isinstance(snapshot["users"]["total"], int)
    assert isinstance(snapshot["apps"]["byType"], list)
