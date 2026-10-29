"""Erros de domínio/aplicação do contexto NC → estados honestos no edge."""

from __future__ import annotations


class NcRepositoryError(Exception):
    """Falha técnica da persistência NC → `unavailable` (502/503 no edge)."""


class NcNotFoundError(Exception):
    """Registro inexistente → 404 no edge."""

    def __init__(self, nonconformity_id: str) -> None:
        super().__init__(f"nonconformity {nonconformity_id} not found")
        self.nonconformity_id = nonconformity_id


class NcValidationError(Exception):
    """Payload inválido → 400 com detalhes de campo."""

    def __init__(self, message: str, fields: dict[str, str] | None = None) -> None:
        super().__init__(message)
        self.fields = fields or {}


class NcConcurrencyError(Exception):
    """Conflito otimista de escrita (ETag/versão) → 409 no edge."""


class NcUnsafeOperationError(Exception):
    """Operação destrutiva fora de contexto autorizado → 403 no edge."""
