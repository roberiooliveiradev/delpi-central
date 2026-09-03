from __future__ import annotations

from dataclasses import dataclass

from requests_app.domain.services.content_loader import engine_reason


@dataclass
class ApplicationError(Exception):
    code: str
    status_code: int = 400
    field: str | None = None

    @property
    def message(self) -> str:
        return engine_reason(self.code, field=self.field)

    def __str__(self) -> str:
        return self.message
