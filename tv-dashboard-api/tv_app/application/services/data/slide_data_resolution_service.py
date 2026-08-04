"""Fachada canônica de resolução de dados de slide TV.

Preview do editor (`TvDataPreviewService`) e payload de apresentação
(`ComunicadoEnrichmentService` → enrich_blocks) compartilham este ponto de
entrada — mesmos `merge_data_params`, fetch e link de views. A apresentação
não tem pipeline paralelo de agregação.
"""

from __future__ import annotations

from typing import Any

from tv_app.application.services.comunicado_data_enrichment_service import (
    ComunicadoDataEnrichmentService,
)
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


class SlideDataResolutionService:
    """Resolve `resolved` nos blocos data_* / views / texto ligado."""

    def __init__(
        self,
        catalog: TvDataRouteCatalogService | None = None,
        enrichment: ComunicadoDataEnrichmentService | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._enrichment = enrichment or ComunicadoDataEnrichmentService(catalog=self._catalog)

    @property
    def enrichment(self) -> ComunicadoDataEnrichmentService:
        return self._enrichment

    def resolve_blocks(
        self,
        blocks: list[dict[str, Any]],
        *,
        cfg: dict[str, Any],
        authorization: str | None = None,
        playlist_defaults: dict[str, Any] | None = None,
        user: Any | None = None,
        force_refresh: bool = False,
        filter_overrides: dict[str, Any] | None = None,
        target_step_name: str | None = None,
        target_source_id: str | None = None,
        preview_options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Mesmo contrato de `ComunicadoDataEnrichmentService.enrich_blocks`."""
        return self._enrichment.enrich_blocks(
            blocks,
            cfg=cfg,
            authorization=authorization,
            playlist_defaults=playlist_defaults,
            user=user,
            force_refresh=force_refresh,
            filter_overrides=filter_overrides,
            target_step_name=target_step_name,
            target_source_id=target_source_id,
            preview_options=preview_options,
        )
