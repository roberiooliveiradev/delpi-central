from __future__ import annotations

from typing import Any

from tv_app.application.services.branch_policy_service import (
    validate_data_route_branch,
    validate_native_branch,
)
from tv_app.application.services.comunicado_input_contract_service import (
    build_input_variable_scope,
    collect_input_variables,
    iter_config_expression_params,
    undeclared_input_reference_issues,
)
from tv_app.application.services.comunicado_native_config_sanitize import (
    sanitize_comunicado_config,
)
from tv_app.application.services.data.data_model_service import (
    collect_native_config_data_routes,
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
from tv_app.application.services.data.m_query.m_expression_interpreter import MExpressionError
from tv_app.application.services.data.value_expression_service import (
    InputVariableScope,
    expression_input_refs,
    validate_expression_param_value,
)
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

        # Contrato de input + refs input.* sobre o nativeConfig candidato inteiro
        # (pós-ops): o mesmo lote pode declarar a variável e a expressão.
        declarations, input_issues = collect_input_variables(blocks)
        issues.extend(input_issues)
        issues.extend(
            undeclared_input_reference_issues(cfg, (item.key for item in declarations))
        )
        input_scope = build_input_variable_scope(blocks)
        issues.extend(self._input_expression_issues(cfg, input_scope))

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
            # Existing v2 transforms remain valid for dual-read compat while M
            # authoring is off. New writes cannot create v2 (writeV2Enabled=false
            # + sanitize_data_transform_for_persistence).
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

        # Rotas dos inputs de DataModel entram no union schema de dataFilters
        # (mesma fonte do runtime/agregador do editor).
        routes_for_filters.extend(
            route
            for route in collect_native_config_data_routes(
                cfg, catalog=self._catalog
            )
            if route not in routes_for_filters
        )

        try:
            if isinstance(data_filters, dict) and data_filters and routes_for_filters:
                validate_data_filters(
                    data_filters, routes=routes_for_filters, input_scope=input_scope
                )
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

    def _input_expression_issues(
        self, cfg: dict[str, Any], input_scope: InputVariableScope
    ) -> list[dict[str, str]]:
        """Expressões de fonte/DataModel que usam ``input.*``: refs/tipos com o escopo do slide."""
        issues: list[dict[str, str]] = []
        for field_path, param, value, operation_id in iter_config_expression_params(cfg):
            if operation_id is None:
                continue
            refs = expression_input_refs(value)
            if not refs or not refs <= set(input_scope.schemas):
                continue
            route = self._catalog.get_route(operation_id)
            if not route:
                continue
            try:
                validate_expression_param_value(
                    param, value, route=route, input_scope=input_scope
                )
            except MExpressionError as exc:
                issues.append({"field": field_path, "message": str(exc), "code": exc.code})
        return issues

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
