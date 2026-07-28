from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar

T = TypeVar("T")


class QueryCachePort(Protocol):
    def get(self, key: str) -> Any | None: ...

    def set(self, key: str, value: Any) -> None: ...

    def invalidate_all(self) -> None: ...

    def get_or_set(self, key: str, factory: Callable[[], T]) -> T:
        """Retorna o valor em cache ou executa ``factory`` uma vez (singleflight)."""
        ...
