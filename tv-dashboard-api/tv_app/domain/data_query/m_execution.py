"""Contratos puros da execução segura de M DELPI."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class MRuntimeError:
    step_name: str
    code: str
    message: str
    row_index: int | None = None
    column: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "stepName": self.step_name,
            "code": self.code,
            "message": self.message,
        }
        if self.row_index is not None:
            payload["rowIndex"] = self.row_index
        if self.column is not None:
            payload["column"] = self.column
        return payload


@dataclass(frozen=True, slots=True)
class MCellError:
    error: MRuntimeError

    def to_public_value(self) -> dict[str, Any]:
        return {"error": self.error.to_dict()}


class MExecutionError(ValueError):
    """Falha estrutural que interrompe a etapa atual."""

    def __init__(self, code: str, message: str, *, step_name: str = "") -> None:
        super().__init__(message)
        self.code = code
        self.step_name = step_name
