"""Erros de domínio do Portal de TI — código estável + status HTTP sugerido."""

from __future__ import annotations


class DomainError(Exception):
    status = 400

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class ValidationError(DomainError):
    status = 422


class NotFoundError(DomainError):
    status = 404


class ConflictError(DomainError):
    status = 409


class PersistenceUnavailableError(DomainError):
    status = 503
