"""Audiência e locale bilíngue — reexport do catálogo de domínio (compat HTTP)."""

from __future__ import annotations

from app.domain.services.route_locale_catalog_service import (
    apply_route_locale_to_x_delpi,
    reset_route_locale_catalog_cache,
    route_locale_for_operation,
    tv_audience_for_operation,
)

# Alias legado usado em testes / scripts.
reset_tv_route_audience_cache = reset_route_locale_catalog_cache

__all__ = [
    "apply_route_locale_to_x_delpi",
    "reset_route_locale_catalog_cache",
    "reset_tv_route_audience_cache",
    "route_locale_for_operation",
    "tv_audience_for_operation",
]
