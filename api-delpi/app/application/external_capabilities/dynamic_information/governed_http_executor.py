"""Compatibility shim — HTTP execution lives in Infrastructure only.

Prefer ``CatalogActionExecutorPort`` + ``AsgiCatalogActionExecutor``.
"""

from __future__ import annotations

from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)

__all__ = ["GovernedExecutionError"]
