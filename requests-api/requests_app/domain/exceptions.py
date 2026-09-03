from __future__ import annotations

from dataclasses import dataclass


@dataclass
class WorkflowEngineError(Exception):
    code: str
    field: str | None = None
    status_code: int = 409

    def __str__(self) -> str:
        return self.code


class RequestTypeNotFoundError(Exception):
    code = "type_not_found"
    status_code = 404

    def __init__(self, type_code: str = "") -> None:
        self.type_code = type_code
        super().__init__(type_code or self.code)
