"""Erros da auditoria de entradas. A rota traduz para o envelope da BFF."""

from __future__ import annotations


class EntryAuditError(Exception):
    def __init__(self, message: str, *, status_code: int, code: str) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.code = code


class XmlSourceUnavailable(Exception):
    """A fonte fiscal falhou. Isso não é ausência de XML."""

    def __init__(self, scope: str) -> None:
        super().__init__(scope)
        self.scope = scope
