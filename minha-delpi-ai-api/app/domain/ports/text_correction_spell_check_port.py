from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TypedDict


class TextCorrectionSpellCheckIssue(TypedDict, total=False):
    offset: int
    length: int
    message: str
    replacements: list[str]
    ruleId: str
    category: str


class TextCorrectionSpellCheckPort(ABC):
    """Verificação ortográfica externa para turnos de correção textual."""

    @abstractmethod
    def check(self, text: str, *, language: str) -> list[TextCorrectionSpellCheckIssue]:
        raise NotImplementedError
