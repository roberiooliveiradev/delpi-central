"""Erros de domínio — Mural de Acessos."""

from __future__ import annotations


class MuralAcessosError(Exception):
    """Erro base do mural de acessos."""


class MuralAcessosNotFoundError(MuralAcessosError):
    """Recurso inexistente."""


class MuralAcessosValidationError(MuralAcessosError):
    """Entrada inválida."""
