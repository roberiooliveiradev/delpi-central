"""Remapeia bindings legados das rotas compostas ROL/OTD para rotas simples."""

from __future__ import annotations

from typing import Any

_COMPOSITE_ROL = "get_commercial_rol"
_COMPOSITE_OTD = "get_commercial_sales_order_otd_analysis"

_FIELD_KEY_REMAP: dict[str, str] = {
    "period_label": "periodo",
    "rol_filial_01": "rol_matrix",
    "rol_filial_02": "rol_branch",
    "otd_pct_filial_01": "otd_filial_01",
    "otd_pct_filial_02": "otd_filial_02",
}

_DROP_PARAMS = frozenset({"group_by", "include"})


def _normalize_mode(display_mode: Any) -> str:
    mode = str(display_mode or "").strip().lower()
    if mode in {"kpi", "line_chart", "table", "auto"}:
        return mode
    return "auto"


def _group_by(params: dict[str, Any]) -> str:
    raw = params.get("group_by")
    value = str(raw or "").strip().lower()
    if value in {"customer", "branch", "none"}:
        return value
    return "customer"


def resolve_simple_commercial_operation_id(
    operation_id: str,
    *,
    display_mode: Any = None,
    params: dict[str, Any] | None = None,
) -> str:
    """Mapeia composta → rota simples conforme displayMode + group_by."""
    op = str(operation_id or "").strip()
    mode = _normalize_mode(display_mode)
    group = _group_by(params if isinstance(params, dict) else {})

    if op == _COMPOSITE_ROL:
        if mode == "kpi":
            return "get_si_indicator_commercial_rol_realized"
        if mode == "line_chart":
            return "get_commercial_rol_series"
        if mode == "table":
            if group == "branch":
                return "get_commercial_rol_by_branch"
            return "get_commercial_rol_by_customer"
        # auto: prioriza série (recorte mais comum do gráfico/tabela temporal)
        if group == "branch":
            return "get_commercial_rol_by_branch"
        if group == "customer":
            return "get_commercial_rol_by_customer"
        return "get_commercial_rol_series"

    if op == _COMPOSITE_OTD:
        if mode == "kpi":
            return "get_sales_order_otd"
        if mode == "line_chart":
            return "get_sales_order_otd_series"
        if mode == "table":
            if group == "branch":
                return "get_sales_order_otd_by_branch"
            return "get_sales_order_otd_by_customer"
        if group == "branch":
            return "get_sales_order_otd_by_branch"
        if group == "customer":
            return "get_sales_order_otd_by_customer"
        return "get_sales_order_otd_series"

    return op


def _remap_string_keys(value: Any) -> Any:
    if isinstance(value, str):
        return _FIELD_KEY_REMAP.get(value, value)
    if isinstance(value, list):
        return [_remap_string_keys(item) for item in value]
    if isinstance(value, dict):
        return {
            _FIELD_KEY_REMAP.get(str(key), key) if isinstance(key, str) else key: _remap_string_keys(item)
            for key, item in value.items()
        }
    return value


_LEGACY_DUAL_COMMERCIAL_ROL: dict[str, tuple[str, str]] = {
    "get_head_office_rol_target_pct": ("get_commercial_rol_summary", "01"),
    "get_branch_rol_target_pct": ("get_commercial_rol_summary", "02"),
    "get_head_office_weg_rol_target_pct": ("get_weg_rol_target_pct", "01"),
    "get_branch_weg_rol_target_pct": ("get_weg_rol_target_pct", "02"),
    "get_head_office_new_business_rol_target_pct": ("get_new_business_rol_target_pct", "01"),
    "get_branch_new_business_rol_target_pct": ("get_new_business_rol_target_pct", "02"),
}


def migrate_dual_commercial_rol_binding(binding: dict[str, Any]) -> dict[str, Any]:
    """Remapeia bindings legados head_office/branch ROL para rotas unificadas + branch."""
    if not isinstance(binding, dict):
        return binding
    operation_id = str(binding.get("operationId") or "").strip()
    mapped = _LEGACY_DUAL_COMMERCIAL_ROL.get(operation_id)
    if not mapped:
        return binding
    next_op, branch = mapped
    next_binding = dict(binding)
    next_binding["operationId"] = next_op
    params_in = binding.get("params") if isinstance(binding.get("params"), dict) else {}
    next_params = {key: value for key, value in params_in.items() if value not in (None, "")}
    next_params["branch"] = branch
    next_binding["params"] = next_params
    return next_binding


def migrate_composite_commercial_binding(binding: dict[str, Any]) -> dict[str, Any]:
    """Atualiza operationId/params/transform de um binding composto para rota simples."""
    if not isinstance(binding, dict):
        return binding
    operation_id = str(binding.get("operationId") or "").strip()
    if operation_id not in {_COMPOSITE_ROL, _COMPOSITE_OTD}:
        return binding

    params_in = binding.get("params") if isinstance(binding.get("params"), dict) else {}
    next_op = resolve_simple_commercial_operation_id(
        operation_id,
        display_mode=binding.get("displayMode"),
        params=params_in,
    )
    next_binding = dict(binding)
    next_binding["operationId"] = next_op

    next_params = {
        key: value
        for key, value in params_in.items()
        if key not in _DROP_PARAMS and value not in (None, "")
    }
    # Séries exigem granularity; se o slide legado não tinha, default week.
    if next_op.endswith("_series") and "granularity" not in next_params:
        next_params["granularity"] = "week"
    # KPI SI / by-branch não usam granularity.
    if not next_op.endswith("_series"):
        next_params.pop("granularity", None)
    next_binding["params"] = next_params

    for transform_key in ("transformSteps", "transformPlan", "viewConfig"):
        if transform_key in next_binding:
            next_binding[transform_key] = _remap_string_keys(next_binding[transform_key])

    return next_binding
