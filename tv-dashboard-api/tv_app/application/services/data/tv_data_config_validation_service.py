from __future__ import annotations

from typing import Any

from tv_app.application.services.branch_policy_service import (
    validate_data_route_branch,
    validate_native_branch,
)
from tv_app.application.services.comunicado_native_config_sanitize import (
    sanitize_comunicado_config,
)
from tv_app.application.services.data.data_transform_contract import (
    DATA_TRANSFORM_V2,
    read_data_transform,
)
from tv_app.application.services.data.m_query.m_query_dependency_service import (
    MQueryDependencyService,
)
from tv_app.application.services.data.tv_data_param_validation_service import (
    validate_data_binding,
    validate_data_filters,
)
from tv_app.application.services.data.tv_data_presentation_modes_service import suggested_display_modes
from tv_app.application.services.tv_data_route_catalog_service import (
    DATA_BLOCK_TYPES,
    TvDataRouteCatalogService,
)
from tv_app.application.services.tv_dashboard_content_service import m_query_setting, message


class TvDataConfigValidationService:
    """Validação canônica de native_config com blocos de dados (save + API /data/validate-config)."""

    def __init__(self, catalog: TvDataRouteCatalogService | None = None) -> None:
        self._catalog = catalog or TvDataRouteCatalogService()

    def sanitize(self, cfg: dict[str, Any] | None) -> dict[str, Any]:
        from tv_app.application.services.data.tv_data_binding_hydrate_service import (
            hydrate_comunicado_data_bindings,
        )

        cleaned = sanitize_comunicado_config(cfg)
        hydrated, _ = hydrate_comunicado_data_bindings(cleaned, catalog=self._catalog)
        return hydrated

    def validate(
        self,
        cfg: dict[str, Any] | None,
        *,
        user: Any | None = None,
    ) -> dict[str, Any]:
        if not isinstance(cfg, dict):
            return {"valid": True, "issues": []}

        issues: list[dict[str, str]] = []
        try:
            validate_native_branch(cfg, user=user)
        except ValueError as exc:
            issues.append({"field": "branch", "message": str(exc)})

        data_filters = cfg.get("dataFilters")
        if isinstance(data_filters, dict) and data_filters.get("branch"):
            try:
                validate_native_branch({"branch": data_filters.get("branch")}, user=user)
            except ValueError as exc:
                issues.append({"field": "dataFilters.branch", "message": str(exc)})

        blocks = cfg.get("blocks")
        if not isinstance(blocks, list):
            return {"valid": len(issues) == 0, "issues": issues, "diagnostics": []}

        routes_for_filters: list[dict[str, Any]] = []
        for index, block in enumerate(blocks):
            if not isinstance(block, dict):
                continue
            block_type = str(block.get("type") or "")
            if block_type not in DATA_BLOCK_TYPES:
                continue
            binding = block.get("dataBinding")
            operation_id = str(binding.get("operationId") or "").strip() if isinstance(binding, dict) else ""
            route = self._catalog.get_route(operation_id)
            if route:
                routes_for_filters.append(route)
            prefix = f"blocks[{index}]"
            transform_result = read_data_transform(block.get("dataTransform"))
            if (
                transform_result.version == DATA_TRANSFORM_V2
                and not bool(m_query_setting("writeV2Enabled", False))
            ):
                issues.append(
                    {
                        "field": f"{prefix}.dataTransform",
                        "message": message("dataTransformV2WriteDisabled"),
                    }
                )
            if not route:
                issues.append(
                    {
                        "field": f"{prefix}.dataBinding.operationId",
                        "message": message("dataSourceUnavailable", "Fonte de dados indisponível."),
                    }
                )
                continue
            try:
                validate_data_binding(
                    binding if isinstance(binding, dict) else None,
                    block_type=block_type,
                    route=route,
                )
            except ValueError as exc:
                issues.append({"field": prefix, "message": str(exc)})
                continue

            params = binding.get("params") if isinstance(binding, dict) and isinstance(binding.get("params"), dict) else {}
            try:
                validate_data_route_branch(route, params, user=user)
            except ValueError as exc:
                issues.append({"field": f"{prefix}.params", "message": str(exc)})

        try:
            if isinstance(data_filters, dict) and data_filters and routes_for_filters:
                validate_data_filters(data_filters, routes=routes_for_filters)
        except ValueError as exc:
            issues.append({"field": "dataFilters", "message": str(exc)})

        graph = MQueryDependencyService().resolve(
            block for block in blocks if isinstance(block, dict)
        )
        diagnostics = list(graph.diagnostics)
        for diagnostic in diagnostics:
            issues.append(
                {
                    "field": "blocks",
                    "message": str(diagnostic.get("message") or "Consulta M inválida."),
                    "code": str(diagnostic.get("code") or "m.invalid"),
                }
            )
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "diagnostics": diagnostics,
            "queryOrder": list(graph.ordered_source_ids),
        }

    def assert_valid(self, cfg: dict[str, Any] | None, *, user: Any | None = None) -> None:
        result = self.validate(cfg, user=user)
        if result["valid"]:
            return
        first = result["issues"][0]
        raise ValueError(first.get("message") or "Configuração de dados inválida.")

    def enrich_route_for_api(self, route: dict[str, Any]) -> dict[str, Any]:
        payload = dict(route)
        payload["suggestedDisplayModes"] = suggested_display_modes(
            allowed_display_modes=route.get("allowedDisplayModes"),
            meta_shape=str(route.get("metaShape") or ""),
        )
        return payload
