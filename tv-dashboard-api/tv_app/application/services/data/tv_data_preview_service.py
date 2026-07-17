from __future__ import annotations

from typing import Any

from tv_app.application.services.comunicado_data_enrichment_service import ComunicadoDataEnrichmentService
from tv_app.application.services.data.tv_data_param_validation_service import validate_data_binding
from tv_app.application.services.data.m_query.m_phase7_quality_service import (
    SafeTelemetry,
    get_cached_preview,
    preview_cache_enabled,
    preview_cache_key,
    set_cached_preview,
)
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
        force_refresh: bool = False,
        target_step_name: str | None = None,
        preview_options: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        block_type = str(block.get("type") or "")
        binding = block.get("dataBinding")
        operation_id = str(binding.get("operationId") or "").strip() if isinstance(binding, dict) else ""
        route = self._catalog.get_route(operation_id)
        validate_data_binding(binding if isinstance(binding, dict) else None, block_type=block_type, route=route)
        cache_key, _principal_fingerprint = preview_cache_key(
            block=block,
            native_config=native_config,
            playlist_defaults=playlist_defaults,
            target_step_name=target_step_name,
            preview_options=preview_options,
            user=user,
            authorization=authorization,
        )
        if not force_refresh and user is not None:
            cached = get_cached_preview(cache_key)
            if cached is not None:
                resolved = cached.get("resolved")
                if isinstance(resolved, dict) and isinstance(resolved.get("query"), dict):
                    resolved["query"]["previewCache"] = "hit"
                SafeTelemetry(
                    "m.preview.cache",
                    0,
                    "hit",
                    artifact_hash=cache_key,
                ).emit()
                return cached
        # Inclui outras fontes do slide para merge (siblingTables) no enrichment.
        target_id = str(block.get("id") or "")
        to_enrich = self._blocks_for_preview(block, native_config)
        enriched = self._enrichment.enrich_blocks(
            to_enrich,
            cfg=native_config,
            authorization=authorization,
            playlist_defaults=playlist_defaults,
            user=user,
            force_refresh=force_refresh,
            target_step_name=target_step_name,
            target_source_id=target_id,
            preview_options=preview_options,
        )
        if not enriched:
            return block
        if target_id:
            for item in enriched:
                if isinstance(item, dict) and str(item.get("id") or "") == target_id:
                    selected = item
                    break
            else:
                selected = enriched[0]
        else:
            selected = enriched[0]
        resolved = selected.get("resolved") if isinstance(selected, dict) else None
        if isinstance(resolved, dict) and isinstance(resolved.get("query"), dict):
            resolved["query"]["previewCache"] = (
                "miss" if preview_cache_enabled() else "disabled"
            )
        if user is not None and isinstance(selected, dict):
            set_cached_preview(cache_key, selected)
        return selected

    @staticmethod
    def _blocks_for_preview(block: dict[str, Any], native_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Bloco alvo + data_sources do slide (necessário para merge entre consultas)."""
        from tv_app.application.services.tv_data_route_catalog_service import DATA_BLOCK_TYPES

        target_id = str(block.get("id") or "")
        out: list[dict[str, Any]] = [block]
        seen = {target_id} if target_id else set()
        cfg_blocks = native_config.get("blocks") if isinstance(native_config, dict) else None
        if not isinstance(cfg_blocks, list):
            return out
        for item in cfg_blocks:
            if not isinstance(item, dict):
                continue
            if str(item.get("type") or "") not in DATA_BLOCK_TYPES:
                continue
            item_id = str(item.get("id") or "")
            if not item_id or item_id in seen:
                continue
            seen.add(item_id)
            # Preferir o payload do request quando for o alvo; demais vêm do cfg.
            out.append(dict(item))
        return out
