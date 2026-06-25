"""Dispatch de builders de commentary por ``builderStrategy`` — Playbook 21 W1b."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from app.domain.services.chat_operational_commentary_profile_service import (
    ChatOperationalCommentaryProfileService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_factory_service import (
    ChatOperationalDataCommentaryFactoryService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_misc_service import (
    ChatOperationalDataCommentaryMiscService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_status_service import (
    ChatOperationalDataCommentaryStatusService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_stock_service import (
    ChatOperationalDataCommentaryStockService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_support_service import (
    ChatOperationalDataCommentarySupportService,
)

_BUILDER_STRATEGIES = frozenset(
    {
        "none",
        "highlight_rules",
        "factory_status",
        "stock",
        "production_status",
        "shipping_status",
        "directives",
        "sale_pricing_insight",
        "analyser_divergence",
    }
)


class ChatOperationalCommentaryBuilderRegistryService:
    @classmethod
    def registered_strategies(cls) -> frozenset[str]:
        return _BUILDER_STRATEGIES

    @classmethod
    def build(
        cls,
        profile_key: str,
        data: dict[str, Any],
        *,
        format_quantity: Callable[[Any, str | None], str] | None = None,
    ) -> dict[str, Any] | None:
        strategy = ChatOperationalCommentaryProfileService.builder_strategy(profile_key)

        if strategy == "none" or not strategy:
            return None

        if strategy == "highlight_rules":
            return ChatOperationalCommentaryProfileService.build_from_highlight_rules(
                profile_key,
                data,
                format_line=ChatOperationalDataCommentarySupportService._presenter_format,
            )

        delegate = cls._delegate_for_strategy(strategy)

        if delegate is None:
            return None

        return delegate(data, format_quantity=format_quantity)

    @classmethod
    def _delegate_for_strategy(
        cls,
        strategy: str,
    ) -> Callable[..., dict[str, Any] | None] | None:
        mapping: dict[str, Callable[..., dict[str, Any] | None]] = {
            "factory_status": ChatOperationalDataCommentaryFactoryService._build_factory_commentary,
            "stock": ChatOperationalDataCommentaryStockService._build_stock_commentary,
            "production_status": ChatOperationalDataCommentaryStatusService._build_production_commentary,
            "shipping_status": ChatOperationalDataCommentaryStatusService._build_shipping_commentary,
            "directives": ChatOperationalDataCommentaryStatusService._build_directives_commentary,
            "sale_pricing_insight": ChatOperationalDataCommentaryMiscService._build_sale_pricing_commentary,
            "analyser_divergence": ChatOperationalDataCommentaryMiscService._build_analyser_commentary,
        }

        return mapping.get(strategy)
