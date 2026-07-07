from __future__ import annotations

from typing import Any

from tv_app.application.services.comunicado_data_enrichment_service import ComunicadoDataEnrichmentService
from tv_app.application.services.data.tv_data_param_validation_service import validate_data_binding
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


class TvDataPreviewService:
    def __init__(
        self,
        catalog: TvDataRouteCatalogService | None = None,
        enrichment: ComunicadoDataEnrichmentService | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._enrichment = enrichment or ComunicadoDataEnrichmentService(catalog=self._catalog)

    def preview_block(
        self,
        block: dict[str, Any],
        *,
        native_config: dict[str, Any],
        authorization: str | None = None,
        user: Any | None = None,
        playlist_defaults: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        block_type = str(block.get("type") or "")
        binding = block.get("dataBinding")
        operation_id = str(binding.get("operationId") or "").strip() if isinstance(binding, dict) else ""
        route = self._catalog.get_route(operation_id)
        validate_data_binding(binding if isinstance(binding, dict) else None, block_type=block_type, route=route)
        enriched = self._enrichment.enrich_blocks(
            [block],
            cfg=native_config,
            authorization=authorization,
            playlist_defaults=playlist_defaults,
            user=user,
        )
        return enriched[0] if enriched else block
