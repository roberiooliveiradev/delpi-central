# app/tests/test_engagement_repository_user_methods.py

from datetime import datetime, timedelta
from unittest.mock import MagicMock
from uuid import uuid4

from app.infrastructure.persistence.sqlalchemy.engagement_repository import (
    SqlAlchemyEngagementRepository,
)


def _scalar_chain(value):
    query = MagicMock()
    query.filter.return_value = query
    query.scalar.return_value = value
    return query


def test_user_usage_summary_returns_zero_for_unknown_user():
    session = MagicMock()
    session.query.side_effect = [
        _scalar_chain(0),
        _scalar_chain(0),
        _scalar_chain(0),
        _scalar_chain(0),
        _scalar_chain(None),
        _scalar_chain(None),
    ]

    repo = SqlAlchemyEngagementRepository(session)
    since = datetime.utcnow() - timedelta(days=30)
    result = repo.user_usage_summary(user_id=uuid4(), since=since)

    assert result == {
        "totalOpens": 0,
        "appsUsed": 0,
        "totalDurationSeconds": 0,
        "portalDurationSeconds": 0,
        "appDurationSeconds": 0,
        "avgSessionSeconds": 0,
        "lastAppUsageAt": None,
    }


def test_user_series_methods_return_empty_for_unknown_user():
    session = MagicMock()
    empty_query = MagicMock()
    empty_query.filter.return_value = empty_query
    empty_query.group_by.return_value = empty_query
    empty_query.order_by.return_value = empty_query
    empty_query.limit.return_value = empty_query
    empty_query.all.return_value = []
    empty_query.scalar.return_value = 0
    session.query.return_value = empty_query

    repo = SqlAlchemyEngagementRepository(session)
    since = datetime.utcnow() - timedelta(days=7)
    user_id = uuid4()

    assert repo.user_opens_by_day(user_id=user_id, since=since) == []
    assert repo.user_duration_by_day(user_id=user_id, since=since) == []
    assert repo.user_apps_by_opens(user_id=user_id, since=since) == []
    assert repo.user_apps_by_duration(user_id=user_id, since=since) == []
    assert repo.user_routes_by_opens(user_id=user_id, since=since) == []
    assert repo.user_count_events_since(user_id=user_id, since=since) == 0
    assert repo.user_count_sessions_since(user_id=user_id, since=since) == 0
