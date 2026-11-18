"""GLPI #887: real SQL checks for bounded weekly app-open aggregation."""

from datetime import datetime, timedelta
from uuid import uuid4

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.infrastructure.db.models import App, AppUsageEvent, User, UserConsent
from app.infrastructure.persistence.sqlalchemy.organization_weekly_usage_repository import (
    SqlAlchemyOrganizationWeeklyUsageRepository,
)


def test_sql_aggregates_only_consented_active_ui_opens_with_exclusive_week_end():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    tables = [
        User.__table__,
        App.__table__,
        UserConsent.__table__,
        AppUsageEvent.__table__,
    ]
    # Test-only schema, no migrations or production DB.
    User.metadata.create_all(bind=engine, tables=tables)
    start = datetime(2026, 11, 9, 3, 0, 0)
    end = datetime(2026, 11, 16, 3, 0, 0)

    with Session(engine) as session:
        opted = uuid4()
        not_opted = uuid4()
        inactive = uuid4()
        session.add_all([
            User(id=opted, name="ATIVO", email="ativo@example.org", active=True),
            User(id=not_opted, name="SEM CONSENTIMENTO", email="sem@example.org", active=True),
            User(id=inactive, name="INATIVO", email="inativo@example.org", active=False),
            App(id="hrdelpi", name="Portal RH", base_path="/rh", type="iframe", active=True),
            App(id="api-delpi", name="API técnica", base_path="/api", type="backend-only", active=True),
            UserConsent(user_id=opted, purpose="usage_tracking", granted=True),
            UserConsent(user_id=not_opted, purpose="usage_tracking", granted=False),
            UserConsent(user_id=inactive, purpose="usage_tracking", granted=True),
        ])
        session.flush()

        for user_id, app_id, timestamp in [
            (opted, "hrdelpi", start),                       # included
            (opted, "hrdelpi", end - timedelta(seconds=1)),# included
            (opted, "hrdelpi", start - timedelta(seconds=1)),# excluded
            (opted, "hrdelpi", end),                         # excluded
            (opted, "api-delpi", start),                     # backend-only excluded
            (not_opted, "hrdelpi", start),                   # no consent excluded
            (inactive, "hrdelpi", start),                    # inactive excluded
        ]:
            session.add(AppUsageEvent(
                id=uuid4(), user_id=user_id, app_id=app_id, opened_at=timestamp,
            ))
        session.flush()

        repo = SqlAlchemyOrganizationWeeklyUsageRepository(session)
        eligible = repo.consented_active_user_ids({opted, not_opted, inactive})
        assert eligible == {opted}

        actual = repo.app_opens(
            user_ids={opted, not_opted, inactive}, since=start, until=end
        )
        assert actual == [{
            "userId": str(opted),
            "appId": "hrdelpi",
            "appName": "Portal RH",
            "count": 2,
        }]
        assert repo.app_opens(user_ids=set(), since=start, until=end) == []


def test_sql_invalid_window_rejected():
    engine = create_engine("sqlite+pysqlite:///:memory:")
    with Session(engine) as session:
        repo = SqlAlchemyOrganizationWeeklyUsageRepository(session)
        try:
            repo.app_opens(
                user_ids={uuid4()},
                since=datetime(2026, 11, 16),
                until=datetime(2026, 11, 9),
            )
        except ValueError as exc:
            assert "Intervalo" in str(exc)
        else:
            raise AssertionError("Intervalo invertido deve ser rejeitado")
