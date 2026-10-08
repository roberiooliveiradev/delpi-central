# tm_app/application/product_guide/product_guide_service.py
"""Read-only application service for Product Usage Guidance.

Guides are guidance only — GUIDANCE_NOT_DOMAIN_TRUTH. This service never
writes, never authorizes and never substitutes for the live contract
(get_catalog) or authoritative domain reads.
"""

from __future__ import annotations

from typing import Any

from tm_app.application.product_guide.product_guide_registry import (
    ProductGuideRegistry,
    get_product_guide_registry,
)
from tm_app.application.product_guide.product_guide_schema import (
    GUIDE_SECTIONS,
    project_section,
)


class ProductGuideNotFoundError(KeyError):
    """Unknown topic — consumer must surface it, never silently substitute."""


class ProductGuideService:
    def __init__(self, registry: ProductGuideRegistry | None = None) -> None:
        self._registry = registry or get_product_guide_registry()

    def get_product_guide(
        self, *, topic: str | None = None, section: str | None = None
    ) -> dict[str, Any]:
        if not topic:
            return {
                "schema": "product_guide_index_v1",
                "registry_version": self._registry.version,
                "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
                "topics": self._registry.index(),
            }
        guide = self._registry.get(str(topic).strip())
        if guide is None:
            raise ProductGuideNotFoundError(
                f"unknown product guide topic {topic!r}; "
                f"available: {self._registry.topic_ids()}"
            )
        if section and section not in GUIDE_SECTIONS:
            raise ValueError(
                f"unknown section {section!r}; expected one of {list(GUIDE_SECTIONS)}"
            )
        return {
            "schema": "product_guide_v1",
            "section": section or "all",
            "guide": project_section(guide, section),
        }
