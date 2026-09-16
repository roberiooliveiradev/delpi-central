"""Compatibility shim — HTTP execution moved to Infrastructure adapter.

Application must not import HTTP clients. Prefer:
  ``execution_plan.build_execution_plan`` + ``CatalogFixedGetPort``.
"""

from __future__ import annotations

from app.application.external_capabilities.dynamic_information.errors import (
    GovernedExecutionError,
)

__all__ = ["GovernedExecutionError"]
