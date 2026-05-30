# app/tests/test_app_usage_ghost_apps.py

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from app.application.use_cases.admin.record_app_usage_use_case import (
    RecordAppUsageUseCase,
)
from app.infrastructure.persistence.sqlalchemy.app_usage_repository import (
    BACKEND_ONLY_APP_TYPE,
    SqlAlchemyAppUsageRepository,
)


def test_ghost_active_apps_excludes_backend_only():
    session = MagicMock()
    repo = SqlAlchemyAppUsageRepository(session)
    filter_conditions: list[object] = []

    def make_query_chain():
        chain = MagicMock()

        def capture_filter(*conditions):
            filter_conditions.extend(conditions)
            return chain

        chain.filter.side_effect = capture_filter
        chain.distinct.return_value = chain
        chain.order_by.return_value = chain
        chain.all.return_value = []
        return chain

    session.query.side_effect = lambda *args, **kwargs: make_query_chain()

    since = datetime.utcnow() - timedelta(days=30)
    repo.ghost_active_apps(since=since)

    serialized = " ".join(str(condition) for condition in filter_conditions)
    assert "apps.type !=" in serialized


def test_record_app_usage_skips_backend_only_from_portal():
    uow = MagicMock()
    use_case = RecordAppUsageUseCase(uow)
    use_case.repo = MagicMock()
    use_case.repo.has_recent_open.return_value = False

    row = MagicMock()
    row.type = BACKEND_ONLY_APP_TYPE
    uow.session.query.return_value.filter.return_value.first.return_value = row

    use_case.execute(
        user_id=str(uuid4()),
        session_id="socket-1",
        app_id="api-delpi",
        route_path="/",
        source="portal",
    )

    use_case.repo.record_open.assert_not_called()
