"""Defaults e caps de paginação operacional (chat → api-delpi) — fonte única JSON."""

from __future__ import annotations

from app.domain.services.chat_assistant_content_service import (
    ChatAssistantContentService,
    invalidate_assistant_content_cache,
)

_BUNDLE = "operational_pagination"


def invalidate_operational_pagination_cache() -> None:
    invalidate_assistant_content_cache(_BUNDLE)


class ChatOperationalPaginationDefaultsService:
    @classmethod
    def _int(cls, *path: str, default: int) -> int:
        node = ChatAssistantContentService.get_node(_BUNDLE, *path)

        try:
            value = int(node)
        except (TypeError, ValueError):
            return default

        return value if value >= 1 else default

    @classmethod
    def standard(cls) -> int:
        return cls._int("tiers", "standard", default=50)

    @classmethod
    def hierarchical(cls) -> int:
        return cls._int("tiers", "hierarchical", default=500)

    @classmethod
    def for_drawing_analyser(cls) -> int:
        return cls._int("tiers", "drawingAnalyser", default=50)

    @classmethod
    def hierarchical_path_markers(cls) -> tuple[str, ...]:
        raw = ChatAssistantContentService.get_node(_BUNDLE, "pathTierMarkers", "hierarchical")

        if not isinstance(raw, list):
            return ("/structure", "/parents")

        markers = tuple(str(item).strip() for item in raw if str(item or "").strip())

        return markers or ("/structure", "/parents")

    @classmethod
    def resolve_for_path(cls, path: str) -> int:
        lowered = str(path or "").lower()

        for marker in cls.hierarchical_path_markers():
            if marker.lower() in lowered:
                return cls.hierarchical()

        return cls.standard()

    @classmethod
    def product_search_default(cls) -> int:
        return cls._int("productSearch", "default", default=5)

    @classmethod
    def product_search_message_cap(cls) -> int:
        return cls._int("productSearch", "messageCap", default=20)

    @classmethod
    def exclusive_catalog_limit(cls) -> int:
        return cls._int("exclusiveCatalogLimit", default=10)

    @classmethod
    def supplies_stock_top_limit(cls) -> int:
        return cls._int("suppliesStockTopLimit", default=10)

    @classmethod
    def refinement_context_fallback(cls) -> int:
        return cls._int("refinementContextFallback", default=25)

    @classmethod
    def auto_recovery_page_size_cap(cls) -> int:
        return cls._int("autoRecoveryPageSizeCap", default=100)

    @classmethod
    def requested_page_size_cap(cls) -> int:
        return cls._int("requestedPageSizeCap", default=500)

    @classmethod
    def agentic_example_page_size(cls) -> int:
        return cls._int("agenticExamplePageSize", default=50)

    @classmethod
    def clamp_requested(cls, value: int) -> int:
        cap = cls.requested_page_size_cap()
        bounded = int(value)

        if bounded < 1:
            return 1

        return min(bounded, cap)
