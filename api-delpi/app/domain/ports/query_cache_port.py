from __future__ import annotations

from typing import Any, Protocol


class QueryCachePort(Protocol):
    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any) -> None: ...

    def invalidate_all(self) -> None: ...
