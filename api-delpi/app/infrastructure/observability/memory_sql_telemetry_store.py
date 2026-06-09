from __future__ import annotations

import threading
from collections import deque

from app.domain.services.sql_query_telemetry_models import SqlQueryRecord


class MemorySqlTelemetryStore:
    def __init__(self, *, max_entries: int = 800) -> None:
        self._max_entries = max(1, int(max_entries))
        self._lock = threading.Lock()
        self._buffer: deque[SqlQueryRecord] = deque(maxlen=self._max_entries)

    def backend_name(self) -> str:
        return "memory"

    def append(self, record: SqlQueryRecord) -> None:
        with self._lock:
            self._buffer.append(record)

    def list_entries(self) -> list[SqlQueryRecord]:
        with self._lock:
            return list(self._buffer)
