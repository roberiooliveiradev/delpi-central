from __future__ import annotations

from typing import Protocol

from app.domain.services.sql_query_telemetry_models import SqlQueryRecord


class SqlTelemetryStorePort(Protocol):
    def backend_name(self) -> str: ...

    def append(self, record: SqlQueryRecord) -> None: ...

    def list_entries(self) -> list[SqlQueryRecord]: ...
