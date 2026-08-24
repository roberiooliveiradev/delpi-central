# app/application/services/usage_session_recorder.py

from __future__ import annotations

from datetime import datetime

from app.application.use_cases.admin.record_usage_session_use_case import (
    RecordUsageSessionUseCase,
)
from app.infrastructure.persistence.sqlalchemy.unit_of_work import SqlAlchemyUnitOfWork


def persist_usage_segment(
    *,
    user_id: str,
    app_id: str | None,
    route_path: str | None,
    started_at: datetime,
    ended_at: datetime,
    source: str,
    socket_session_id: str | None = None,
) -> None:
    try:
        with SqlAlchemyUnitOfWork() as uow:
            recorded = RecordUsageSessionUseCase(uow).execute(
                user_id=user_id,
                app_id=app_id,
                route_path=route_path,
                started_at=started_at,
                ended_at=ended_at,
                source=source,
                socket_session_id=socket_session_id,
            )
            if recorded:
                uow.commit()
    except Exception as exc:
        print("⚠️ persist_usage_segment failed:", repr(exc))
