# tv_app/application/product_guide/product_guide_service.py
"""Read-only application service for TV Dashboard Product Guidance.

Guides are guidance only — GUIDANCE_NOT_DOMAIN_TRUTH. This service never
writes, never authorizes and never substitutes for the live contract
(get_catalog / capability surface), api-delpi/OpenAPI data contracts or
authoritative domain reads.
"""

from __future__ import annotations

from typing import Any

from tv_app.application.product_guide.product_guide_registry import (
    ProductGuideRegistry,
    get_product_guide_registry,
)
from tv_app.application.product_guide.product_guide_schema import (
    GUIDE_SECTIONS,
    project_section,
)

# Fields safe to render in user-facing help — internal refs
# (capability_refs/operation_refs/read_refs/write_refs/source_refs/
# agent_guidance/schema) never leave the backend.
HELP_VIEW_FIELDS = (
    "id",
    "title",
    "summary",
    "purpose",
    "use_when",
    "do_not_use_when",
    "how_to_use",
    "field_guidance",
    "quality_rules",
    "common_mistakes",
    "related_topics",
)


def to_help_view(guide: dict[str, Any]) -> dict[str, Any]:
    return {
        k: guide[k]
        for k in HELP_VIEW_FIELDS
        if guide.get(k) not in (None, [], {})
    }


def guide_index_payload(registry: ProductGuideRegistry) -> dict[str, Any]:
    """Compact discovery index — embeddable in get_catalog (MCP projection).

    Topic bodies are never embedded: they are fetched on demand via
    ``get_product_guide``. The Actions envelope sits at the OpenAI ~100 KiB
    ceiling, so this index is MCP-primary — Actions discovers the capability
    through ``gpt_get_product_guide`` and ``capability_surface`` instead.
    """
    return {
        "schema": "product_guide_index_v1",
        "registryVersion": registry.version,
        "authority": "GUIDANCE_NOT_DOMAIN_TRUTH",
        "sections": list(GUIDE_SECTIONS),
        "readCapability": "get_product_guide",
        "topics": registry.index(),
    }


class ProductGuideNotFoundError(LookupError):
    """Unknown topic — consumer must surface it, never silently substitute."""


class ProductGuideService:
    def __init__(self, registry: ProductGuideRegistry | None = None) -> None:
        self._registry = registry or get_product_guide_registry()

    def get_product_guide(
        self, *, topic: str | None = None, section: str | None = None
    ) -> dict[str, Any]:
        if not topic:
            return guide_index_payload(self._registry)
        guide = self._registry.get(str(topic).strip())
        if guide is None:
            raise ProductGuideNotFoundError(
                f"unknown product guide topic {topic!r}; "
                f"available: {self._registry.topic_ids()}"
            )
        if section and section not in GUIDE_SECTIONS:
            raise ValueError(
                f"unknown section {section!r}; "
                f"expected one of {list(GUIDE_SECTIONS)}"
            )
        return {
            "schema": "product_guide_v1",
            "section": section or "all",
            "guide": project_section(guide, section),
        }

    def get_help_view(self, *, topic: str | None = None) -> dict[str, Any]:
        """Portal Help projection — public fields only, full guide."""
        if topic:
            guide = self._registry.get(str(topic).strip())
            if guide is None:
                raise ProductGuideNotFoundError(
                    f"unknown product guide topic {topic!r}; "
                    f"available: {self._registry.topic_ids()}"
                )
            return {
                "schema": "product_guide_help_v1",
                "registryVersion": self._registry.version,
                "topic": to_help_view(guide),
            }
        return {
            "schema": "product_guide_help_v1",
            "registry_version": self._registry.version,
            "topics": [
                to_help_view(self._registry.get(t))
                for t in self._registry.topic_ids()
            ],
        }
