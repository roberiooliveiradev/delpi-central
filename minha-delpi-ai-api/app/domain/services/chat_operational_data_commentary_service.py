"""Comentário e análise de dados operacionais — desacoplado de presenters e agentes."""

from __future__ import annotations

from typing import Any, Callable

from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_factory_service import (
    ChatOperationalDataCommentaryFactoryService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_misc_service import (
    ChatOperationalDataCommentaryMiscService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_orchestration_service import (
    ChatOperationalDataCommentaryOrchestrationService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_profile_resolver_service import (
    ChatOperationalDataCommentaryProfileResolverService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_status_service import (
    ChatOperationalDataCommentaryStatusService,
)
from app.domain.services.chat_operational_data_commentary.chat_operational_data_commentary_stock_service import (
    ChatOperationalDataCommentaryStockService,
)

__all__ = ["ChatOperationalDataCommentaryService"]


class ChatOperationalDataCommentaryService:
    """Fachada — comentário operacional por perfil (estoque, fábrica, produção, …)."""

    @classmethod
    def resolve_profile_key(cls, *args, **kwargs) -> str | None:
        return ChatOperationalDataCommentaryProfileResolverService.resolve_profile_key(
            *args, **kwargs
        )

    @classmethod
    def build(cls, *args, **kwargs) -> dict[str, Any] | None:
        return ChatOperationalDataCommentaryOrchestrationService.build(*args, **kwargs)

    @classmethod
    def render_markdown_sections(cls, commentary: dict[str, Any] | None) -> str:
        return ChatOperationalDataCommentaryOrchestrationService.render_markdown_sections(
            commentary
        )

    @classmethod
    def aggregate_mp_stock_rows(cls, stock_items: object) -> list[dict[str, Any]]:
        return ChatOperationalDataCommentaryFactoryService.aggregate_mp_stock_rows(stock_items)

    # --- Delegates privados (orquestração cross-perfil) ---

    @classmethod
    def _build_factory_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryFactoryService._build_factory_commentary(
            *args, **kwargs
        )

    @classmethod
    def _build_stock_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryStockService._build_stock_commentary(*args, **kwargs)

    @classmethod
    def _build_production_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryStatusService._build_production_commentary(
            *args, **kwargs
        )

    @classmethod
    def _build_shipping_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryStatusService._build_shipping_commentary(
            *args, **kwargs
        )

    @classmethod
    def _build_directives_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryStatusService._build_directives_commentary(
            *args, **kwargs
        )

    @classmethod
    def _build_sale_pricing_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryMiscService._build_sale_pricing_commentary(
            *args, **kwargs
        )

    @classmethod
    def _build_structure_exclusivity_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryMiscService._build_structure_exclusivity_commentary(
            *args, **kwargs
        )

    @classmethod
    def _build_analyser_commentary(cls, *args, **kwargs):
        return ChatOperationalDataCommentaryMiscService._build_analyser_commentary(
            *args, **kwargs
        )
