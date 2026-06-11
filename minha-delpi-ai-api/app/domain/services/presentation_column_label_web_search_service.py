"""Facade de domain para busca web na descoberta de rótulos de coluna."""

from __future__ import annotations

from typing import ClassVar

from app.domain.ports.presentation_column_label_web_search_port import (
    PresentationColumnLabelWebSearchPort,
)


class PresentationColumnLabelWebSearchService:
    _port: ClassVar[PresentationColumnLabelWebSearchPort | None] = None

    @classmethod
    def configure(cls, port: PresentationColumnLabelWebSearchPort) -> None:
        cls._port = port

    @classmethod
    def search(cls, query: str, *, max_results: int = 2) -> dict | None:
        if cls._port is None:
            return None

        try:
            return cls._port.search(query, max_results=max_results)
        except Exception:
            return None
