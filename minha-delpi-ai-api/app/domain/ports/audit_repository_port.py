from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AuditLogQuery:
    limit: int = 50
    offset: int = 0
    action: str | None = None
    context: str | None = None
    user_id: UUID | None = None
    trace_id: str | None = None
    search: str | None = None
    date_from: datetime | None = None
    date_to: datetime | None = None


class AuditRepositoryPort(ABC):
    @abstractmethod
    def log(
        self,
        user_id: UUID | None,
        action: str,
        prompt_hash: str | None = None,
        context: str | None = None,
        tool_calls: list | None = None,
        metadata: dict | None = None,
    ) -> None:
        raise NotImplementedError

    @abstractmethod
    def list_logs_page(self, query: AuditLogQuery) -> tuple[list[dict], int]:
        raise NotImplementedError

    @abstractmethod
    def get_log(self, log_id: int) -> dict | None:
        raise NotImplementedError

    @abstractmethod
    def list_by_prompt_hash(
        self,
        *,
        prompt_hash: str,
        limit: int = 20,
        exclude_id: int | None = None,
    ) -> list[dict]:
        raise NotImplementedError

    def list_by_trace_id(
        self,
        *,
        trace_id: str,
        limit: int = 20,
        exclude_id: int | None = None,
    ) -> list[dict]:
        raise NotImplementedError

    def get_timeline_summary(
        self,
        query: AuditLogQuery,
        *,
        max_days: int = 31,
    ) -> dict:
        raise NotImplementedError

    def get_drawing_analysis_summary(self, *, hours: int = 168) -> dict:
        raise NotImplementedError

    def get_document_vision_summary(self, *, hours: int = 168) -> dict:
        raise NotImplementedError

    def get_intent_routing_summary(self, *, hours: int = 168) -> dict:
        raise NotImplementedError

    def get_text_task_summary(self, *, hours: int = 168) -> dict:
        raise NotImplementedError

    def get_interactivity_summary(self, *, hours: int = 168) -> dict:
        raise NotImplementedError

    def get_error_handling_summary(self, *, hours: int = 168) -> dict:
        raise NotImplementedError

    def get_web_search_summary(self, *, hours: int = 168) -> dict:
        raise NotImplementedError

    def list_logs(self, limit: int = 100) -> list[dict]:
        items, _total = self.list_logs_page(AuditLogQuery(limit=limit, offset=0))
        return items
