from __future__ import annotations

from typing import Any

from tv_app.application.services.branch_policy_service import validate_native_branch
from tv_app.application.services.tv_data_route_catalog_service import (
    DATA_BLOCK_TYPES,
    TvDataRouteCatalogService,
)
from tv_app.application.services.tv_dashboard_content_service import (
    message,
    tv_dashboard_setting_int,
)


def max_data_blocks_per_slide() -> int:
    return tv_dashboard_setting_int("comunicadoDataBlocksMaxPerSlide", 6)


def _strip_runtime_fields(block: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(block)
    cleaned.pop("resolved", None)
    cleaned.pop("url", None)
    return cleaned


def sanitize_comunicado_config(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Remove campos de runtime (resolved, url) antes de persistir native_config."""
    if not isinstance(cfg, dict):
        return {}
    result = dict(cfg)
    blocks_raw = result.get("blocks")
    if isinstance(blocks_raw, list):
        result["blocks"] = [
            _strip_runtime_fields(block) for block in blocks_raw if isinstance(block, dict)
        ]
    background = result.get("background")
    if isinstance(background, dict) and background.get("type") == "image":
        bg = dict(background)
        bg.pop("url", None)
        result["background"] = bg
    return result


def validate_comunicado_native_config(
    cfg: dict[str, Any] | None,
    *,
    user: Any | None = None,
    catalog: TvDataRouteCatalogService | None = None,
) -> None:
    """Valida allowlist, limite de blocos data_* e RBAC de filial em filtros/params."""
    if not isinstance(cfg, dict):
        return

    validate_native_branch(cfg, user=user)

    data_filters = cfg.get("dataFilters")
    if isinstance(data_filters, dict) and data_filters.get("branch"):
        validate_native_branch({"branch": data_filters.get("branch")}, user=user)

    blocks = cfg.get("blocks")
    if not isinstance(blocks, list):
        return

    catalog_service = catalog or TvDataRouteCatalogService()
    data_block_count = 0

    for block in blocks:
        if not isinstance(block, dict):
            continue
        block_type = str(block.get("type") or "")
        if block_type not in DATA_BLOCK_TYPES:
            continue
        data_block_count += 1
        binding = block.get("dataBinding")
        if not isinstance(binding, dict):
            raise ValueError(message("dataIndicatorUnavailable", "Indicador indisponível"))
        operation_id = str(binding.get("operationId") or "").strip()
        if not catalog_service.is_allowed(operation_id):
            raise ValueError(message("dataIndicatorUnavailable", "Indicador indisponível"))
        params = binding.get("params")
        if isinstance(params, dict) and params.get("branch"):
            validate_native_branch({"branch": params.get("branch")}, user=user)

    if data_block_count > max_data_blocks_per_slide():
        raise ValueError(message("dataBlocksLimitExceeded", "Limite de indicadores por slide excedido."))
