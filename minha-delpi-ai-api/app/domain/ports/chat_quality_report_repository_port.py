from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime


class ChatQualityReportRepositoryPort(ABC):
    @abstractmethod
    def create(
        self,
        *,
        report_type: str,
        period_start: datetime,
        period_end: datetime,
        summary_json: dict,
        markdown: str,
    ) -> dict:
        raise NotImplementedError

    @abstractmethod
    def get_latest(self, *, report_type: str = "weekly") -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_recent(self, *, report_type: str = "weekly", limit: int = 12) -> list[dict]:
        raise NotImplementedError
