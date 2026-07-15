"""Erros de domínio — Guias e Procedimentos (admin)."""

from __future__ import annotations


class GuiasProcedimentosError(Exception):
    """Erro base do módulo."""


class GuiasValidationError(GuiasProcedimentosError):
    """Payload inválido (HTTP 422)."""


class GuiasConflictError(GuiasProcedimentosError):
    """Conflito de recurso, ex.: slug duplicado (HTTP 409)."""


class GuiasNotFoundError(GuiasProcedimentosError):
    """Recurso inexistente (HTTP 404)."""
