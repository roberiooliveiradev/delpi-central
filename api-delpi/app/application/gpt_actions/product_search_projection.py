"""Fail-closed projection — re-export from provider-neutral external_capabilities."""

from app.application.external_capabilities.product_search_projection import (
    project_product_search_item,
    project_product_search_page,
)

__all__ = [
    "project_product_search_item",
    "project_product_search_page",
]
