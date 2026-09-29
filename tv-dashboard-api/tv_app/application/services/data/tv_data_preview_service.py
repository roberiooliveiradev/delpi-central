from __future__ import annotations

from typing import Any

from tv_app.application.services.comunicado_data_enrichment_service import ComunicadoDataEnrichmentService
from tv_app.application.services.data.slide_data_resolution_service import SlideDataResolutionService
from tv_app.application.services.data.tv_data_param_validation_service import validate_data_binding
from tv_app.application.services.data.m_query.m_phase7_quality_service import (
    SafeTelemetry,
    get_cached_preview,
    preview_cache_enabled,
    preview_cache_key,
    set_cached_preview,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    TvDataRouteCatalogService,
    normalize_data_binding_operation_id,
)


def _binding_target(node: dict[str, Any]) -> str:
    """modelId > dataSourceId — mesmo dual-read do link canônico (DM2)."""
    from tv_app.application.services.data.projection_fields_contract import (
        binding_target_id,
    )

    return binding_target_id(node)


class TvDataPreviewService:
    def __init__(
        self,
        catalog: TvDataRouteCatalogService | None = None,
        enrichment: ComunicadoDataEnrichmentService | None = None,
        resolution: SlideDataResolutionService | None = None,
    ) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()
        self._enrichment = enrichment or ComunicadoDataEnrichmentService(catalog=self._catalog)
        self._resolution = resolution or SlideDataResolutionService(
            catalog=self._catalog,
            enrichment=self._enrichment,
        )

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
        binding = normalize_data_binding_operation_id(
            block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else None
        )
        if binding is not None and binding is not block.get("dataBinding"):
            block = {**block, "dataBinding": binding}
        operation_id = str(binding.get("operationId") or "").strip() if isinstance(binding, dict) else ""
        route = self._catalog.get_route(operation_id)
        # Estrutura do binding (rota, displayMode). Params obrigatórios e período
        # herdáveis (programação/tela) só após merge_data_params no enrichment/gateway.
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
                cached_resolved = (
                    cached.get("resolved") if isinstance(cached, dict) else None
                )
                # Contract FE-BE-002: editor needs linkedResolvedByBlockId. Old cache = miss.
                if isinstance(cached_resolved, dict) and (
                    "linkedResolvedByBlockId" in cached_resolved
                    or not self._native_config_has_linked_views(native_config, target_id=str(block.get("id") or ""))
                ):
                    if isinstance(cached_resolved.get("query"), dict):
                        cached_resolved["query"]["previewCache"] = "hit"
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
        # Mesma fachada que o payload de apresentação (viewer puro).
        enriched = self._resolution.resolve_blocks(
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
        # Editor paints views/text from source preview — attach per-block enrich
        # (display*/projection bake) so paint is not raw source.resolved (FE-BE-002).
        selected = self._attach_linked_resolved_for_editor(selected, enriched, target_id)
        resolved = selected.get("resolved") if isinstance(selected, dict) else None
        if isinstance(resolved, dict) and isinstance(resolved.get("query"), dict):
            resolved["query"]["previewCache"] = (
                "miss" if preview_cache_enabled() else "disabled"
            )
        if user is not None and isinstance(selected, dict):
            set_cached_preview(cache_key, selected)
        return selected

    def resolve_blocks(
        self,
        blocks: list[dict[str, Any]],
        *,
        native_config: dict[str, Any],
        authorization: str | None = None,
        user: Any | None = None,
        playlist_defaults: dict[str, Any] | None = None,
        force_refresh: bool = False,
        target_step_name: str | None = None,
        preview_options: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        """Bounded enrich of an explicit block set — same canonical resolver as
        `preview_block` (params merge, expression resolution, fetch, transform
        DAG, linked views). Used by read-only inspection flows that must scope
        execution to a dependency closure instead of the whole slide."""
        return self._resolution.resolve_blocks(
            blocks,
            cfg=native_config,
            authorization=authorization,
            playlist_defaults=playlist_defaults,
            user=user,
            force_refresh=force_refresh,
            target_step_name=target_step_name,
            preview_options=preview_options,
        )

    def preview_data_model(
        self,
        model: dict[str, Any],
        *,
        native_config: dict[str, Any],
        authorization: str | None = None,
        user: Any | None = None,
        playlist_defaults: dict[str, Any] | None = None,
        force_refresh: bool = False,
    ) -> dict[str, Any]:
        """Preview de DataModel — mesmo resolver do enrichment (sem persistir)."""
        resolved_map = self._resolution.enrich_data_models(
            [model],
            cfg=native_config,
            authorization=authorization,
            playlist_defaults=playlist_defaults,
            user=user,
            force_refresh=force_refresh,
        )
        model_id = str(model.get("id") or "")
        resolved = resolved_map.get(model_id)
        if not isinstance(resolved, dict):
            resolved = next(
                (r for r in resolved_map.values() if isinstance(r, dict)),
                {"error": "Modelo não resolvido."},
            )
        # FE-BE-002 (model variant): editor paints views/text from the model
        # preview — attach per-block enrich so linked visuals resolve by own id.
        if model_id:
            resolved = self._attach_linked_resolved_for_model(
                resolved,
                native_config,
                model_resolved={model_id: resolved},
                model_id=model_id,
            )
        return resolved

    @staticmethod
    def _attach_linked_resolved_for_model(
        resolved: dict[str, Any],
        native_config: dict[str, Any],
        *,
        model_resolved: dict[str, dict[str, Any]],
        model_id: str,
    ) -> dict[str, Any]:
        """Stamp linkedResolvedByBlockId on the model preview for editor paint."""
        cfg_blocks = (
            native_config.get("blocks")
            if isinstance(native_config, dict)
            else None
        )
        if not isinstance(cfg_blocks, list):
            return resolved
        linked_blocks = (
            ComunicadoDataEnrichmentService._link_view_blocks_to_sources(
                [block for block in cfg_blocks if isinstance(block, dict)],
                model_resolved=model_resolved,
            )
        )
        linked: dict[str, Any] = {}
        for item in linked_blocks:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or "").strip()
            item_resolved = item.get("resolved")
            if not item_id or not isinstance(item_resolved, dict):
                continue
            if _binding_target(item) == model_id:
                linked[item_id] = item_resolved
                continue
            if str(item.get("type") or "") == "canvas_table":
                by_source = item.get("resolvedBySourceId")
                if isinstance(by_source, dict) and model_id in by_source:
                    linked[item_id] = item_resolved
        if not linked:
            return resolved
        next_resolved = dict(resolved)
        next_resolved["linkedResolvedByBlockId"] = linked
        return next_resolved

    @staticmethod
    def _attach_linked_resolved_for_editor(
        selected: dict[str, Any],
        enriched: list[dict[str, Any]],
        target_id: str,
    ) -> dict[str, Any]:
        """Stamp linkedResolvedByBlockId on the previewed source for editor paint."""
        if not isinstance(selected, dict):
            return selected
        target = str(target_id or selected.get("id") or "").strip()
        if not target:
            return selected
        linked: dict[str, Any] = {}
        for item in enriched:
            if not isinstance(item, dict):
                continue
            item_id = str(item.get("id") or "").strip()
            if not item_id or item_id == target:
                continue
            resolved = item.get("resolved")
            if not isinstance(resolved, dict):
                continue
            # Direct link to this source/model (modelId > dataSourceId).
            if _binding_target(item) == target:
                linked[item_id] = resolved
                continue
            # Canvas table may bind cells to this source.
            if str(item.get("type") or "") == "canvas_table":
                by_source = item.get("resolvedBySourceId")
                if isinstance(by_source, dict) and target in by_source:
                    linked[item_id] = resolved
        # Always stamp the map (possibly empty) so cache contract is detectable.
        next_selected = dict(selected)
        next_resolved = (
            dict(selected["resolved"])
            if isinstance(selected.get("resolved"), dict)
            else {}
        )
        next_resolved["linkedResolvedByBlockId"] = linked
        next_selected["resolved"] = next_resolved
        return next_selected

    @staticmethod
    def _native_config_has_linked_views(
        native_config: dict[str, Any] | None,
        *,
        target_id: str,
    ) -> bool:
        """True when the slide has views/text/canvas that bind to this source."""
        from tv_app.application.services.tv_data_route_catalog_service import (
            CANVAS_TABLE_DATA_BOUND_BLOCK_TYPES,
            DATA_VIEW_BLOCK_TYPES,
            TEXT_DATA_BOUND_BLOCK_TYPES,
        )

        target = str(target_id or "").strip()
        if not target or not isinstance(native_config, dict):
            return False
        cfg_blocks = native_config.get("blocks")
        if not isinstance(cfg_blocks, list):
            return False
        view_types = DATA_VIEW_BLOCK_TYPES | TEXT_DATA_BOUND_BLOCK_TYPES | CANVAS_TABLE_DATA_BOUND_BLOCK_TYPES
        for item in cfg_blocks:
            if not isinstance(item, dict):
                continue
            if str(item.get("type") or "") not in view_types:
                continue
            if _binding_target(item) == target:
                return True
            if str(item.get("type") or "") == "canvas_table":
                cells = item.get("cells")
                if isinstance(cells, list):
                    for row in cells:
                        if not isinstance(row, list):
                            continue
                        for cell in row:
                            if (
                                isinstance(cell, dict)
                                and _binding_target(cell) == target
                            ):
                                return True
        return False

    @staticmethod
    def _blocks_for_preview(block: dict[str, Any], native_config: dict[str, Any]) -> list[dict[str, Any]]:
        """Alvo + fontes do slide + views/texto/canvas ligados (enrich display* no preview)."""
        from tv_app.application.services.tv_data_route_catalog_service import (
            CANVAS_TABLE_DATA_BOUND_BLOCK_TYPES,
            DATA_BLOCK_TYPES,
            DATA_VIEW_BLOCK_TYPES,
            TEXT_DATA_BOUND_BLOCK_TYPES,
        )

        target_id = str(block.get("id") or "")
        out: list[dict[str, Any]] = [block]
        seen = {target_id} if target_id else set()
        cfg_blocks = native_config.get("blocks") if isinstance(native_config, dict) else None
        if not isinstance(cfg_blocks, list):
            return out

        linkable = (
            DATA_BLOCK_TYPES
            | DATA_VIEW_BLOCK_TYPES
            | TEXT_DATA_BOUND_BLOCK_TYPES
            | CANVAS_TABLE_DATA_BOUND_BLOCK_TYPES
        )

        for item in cfg_blocks:
            if not isinstance(item, dict):
                continue
            item_type = str(item.get("type") or "")
            if item_type not in linkable:
                continue
            item_id = str(item.get("id") or "")
            if not item_id or item_id in seen:
                continue
            # Sibling sources + all views/text/canvas so enrich can bake display*.
            seen.add(item_id)
            out.append(dict(item))
        return out
