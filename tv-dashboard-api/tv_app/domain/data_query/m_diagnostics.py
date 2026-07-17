"""Diagnósticos imutáveis do domínio de consultas M DELPI."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


@dataclass(frozen=True, slots=True)
class SourceRange:
    """Intervalo 1-based, com fim exclusivo, dentro do script de origem."""

    start_line: int
    start_column: int
    end_line: int
    end_column: int
    start_offset: int
    end_offset: int

    def __post_init__(self) -> None:
        if min(self.start_line, self.start_column, self.end_line, self.end_column) < 1:
            raise ValueError("Linhas e colunas de SourceRange são 1-based.")
        if (self.end_line, self.end_column) < (self.start_line, self.start_column):
            raise ValueError("Fim de SourceRange não pode preceder o início.")
        if self.start_offset < 0 or self.end_offset < self.start_offset:
            raise ValueError("Offsets inválidos em SourceRange.")

    def to_dict(self) -> dict[str, int]:
        return {
            "startLine": self.start_line,
            "startColumn": self.start_column,
            "endLine": self.end_line,
            "endColumn": self.end_column,
            "startOffset": self.start_offset,
            "endOffset": self.end_offset,
        }


class DiagnosticSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass(frozen=True, slots=True)
class Diagnostic:
    code: str
    severity: DiagnosticSeverity
    message: str
    source_range: SourceRange | None = None
    hint: str | None = None

    def __post_init__(self) -> None:
        if not self.code.strip():
            raise ValueError("Diagnostic.code é obrigatório.")
        if not self.message.strip():
            raise ValueError("Diagnostic.message é obrigatória.")

    def to_dict(self) -> dict[str, object]:
        payload: dict[str, object] = {
            "code": self.code,
            "severity": self.severity.value,
            "message": self.message,
        }
        if self.source_range is not None:
            payload["range"] = self.source_range.to_dict()
        if self.hint:
            payload["hint"] = self.hint
        return payload
