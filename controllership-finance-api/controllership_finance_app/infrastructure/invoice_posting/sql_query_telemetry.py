"""Telemetry stub — preserves timed_sql_query call sites without api-delpi import."""

from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator


@contextmanager
def timed_sql_query(repository: str, query: str) -> Iterator[None]:
    yield
