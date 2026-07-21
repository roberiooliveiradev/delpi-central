from __future__ import annotations

from typing import Any

from tv_app.application.services.comunicado_native_config_sanitize import (
    sanitize_comunicado_config,
)
from tv_app.application.services.data.tv_data_config_validation_service import TvDataConfigValidationService
from tv_app.application.services.tv_data_route_catalog_service import TvDataRouteCatalogService


def validate_comunicado_native_config(
    cfg: dict[str, Any] | None,
    *,
    user: Any | None = None,
    catalog: TvDataRouteCatalogService | None = None,
) -> None:
    """Valida allowlist, params, formatos e RBAC de blocos de dados."""
    TvDataConfigValidationService(catalog=catalog).assert_valid(cfg, user=user)


__all__ = [
    "sanitize_comunicado_config",
    "validate_comunicado_native_config",
]
