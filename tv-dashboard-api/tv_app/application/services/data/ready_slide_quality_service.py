"""Gates de qualidade para slide composto pronto (params / projection / resolved.error)."""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.data.tv_data_param_validation_service import (
    assert_closed_date_range_has_period,
    closed_date_range_missing_filter_labels,
)
from tv_app.application.services.tv_date_range_preset_service import DATE_RANGE_PRESET_KEY

_DATA_VISUAL_TYPES = frozenset(
    {
        "kpi_view",
        "data_kpi",
        "chart_view",
        "data_chart",
        "table_view",
        "data_table",
    }
)


class ReadySlideQualityService:
    """Owner de regras que impedem VERIFIED mentiroso / fonte date_range vazia."""

    DEFAULT_DATE_RANGE_PRESET = "this_month"

    @classmethod
    def is_closed_date_range_route(cls, route: Mapping[str, Any] | None) -> bool:
        if not isinstance(route, dict):
            return False
        if str(route.get("paramStrategy") or "").strip() != "date_range":
            return False
        return not bool(route.get("openEndedDateRange"))

    @classmethod
    def enrich_data_source_params(
        cls,
        route: Mapping[str, Any] | None,
        params: Mapping[str, Any] | None,
        *,
        playlist_defaults: Mapping[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Injeta dateRangePreset/branch tipados quando ausentes (sem inventar filial)."""
        out = dict(params or {})
        defaults = playlist_defaults if isinstance(playlist_defaults, dict) else {}
        if cls.is_closed_date_range_route(route):
            labels = closed_date_range_missing_filter_labels(route)
            if labels:
                # Ainda falta período → preset canônico.
                try:
                    assert_closed_date_range_has_period(route, out)
                except ValueError:
                    if not out.get(DATE_RANGE_PRESET_KEY) and not out.get("periodDays"):
                        out[DATE_RANGE_PRESET_KEY] = cls.DEFAULT_DATE_RANGE_PRESET
        if "branch" not in out and defaults.get("branch") not in (None, ""):
            out["branch"] = defaults.get("branch")
        return out

    @classmethod
    def assert_data_source_params_ready(
        cls,
        route: Mapping[str, Any] | None,
        params: Mapping[str, Any] | None,
    ) -> None:
        """Raise ValueError se rota date_range fechada sem período."""
        if not cls.is_closed_date_range_route(route):
            return
        assert_closed_date_range_has_period(route, dict(params or {}))

    @classmethod
    def projection_is_empty(cls, block: Mapping[str, Any]) -> bool:
        block_type = str(block.get("type") or "")
        if block_type not in _DATA_VISUAL_TYPES:
            return False
        if block_type in {"kpi_view", "data_kpi"}:
            proj = block.get("kpiProjection")
            if isinstance(proj, dict):
                metrics = proj.get("metrics")
                if isinstance(metrics, list) and metrics:
                    return False
                if proj.get("valueField") or proj.get("field"):
                    return False
            return True
        if block_type in {"chart_view", "data_chart"}:
            proj = block.get("chartProjection")
            if isinstance(proj, dict) and (
                proj.get("xField")
                or proj.get("yField")
                or proj.get("seriesField")
                or (isinstance(proj.get("series"), list) and proj.get("series"))
            ):
                return False
            return True
        if block_type in {"table_view", "data_table"}:
            proj = block.get("tableProjection")
            if isinstance(proj, dict):
                cols = proj.get("columns")
                if isinstance(cols, list) and cols:
                    return False
            return True
        return False

    @classmethod
    def collect_native_quality_issues(
        cls,
        native_config: Mapping[str, Any] | None,
        *,
        catalog: Any | None = None,
    ) -> list[str]:
        """Lista códigos de problema em nativeConfig (vazio = OK)."""
        issues: list[str] = []
        if not isinstance(native_config, dict):
            return issues
        blocks = native_config.get("blocks")
        if not isinstance(blocks, list):
            return issues
        for block in blocks:
            if not isinstance(block, dict):
                continue
            resolved = block.get("resolved")
            if isinstance(resolved, dict) and resolved.get("error"):
                issues.append(f"resolved.error:{block.get('id') or block.get('type')}")
            binding = block.get("dataBinding")
            if isinstance(binding, dict) and catalog is not None:
                op_id = str(binding.get("operationId") or "").strip()
                if op_id:
                    route = catalog.get_route(op_id) if hasattr(catalog, "get_route") else None
                    params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
                    try:
                        cls.assert_data_source_params_ready(route, params)
                    except ValueError:
                        issues.append(f"params.incomplete:{op_id}")
            if str(block.get("type") or "") in _DATA_VISUAL_TYPES:
                # Só exige projection se o visual está bound a uma fonte.
                has_bind = bool(
                    str(block.get("dataSourceId") or "").strip()
                    or (
                        isinstance(block.get("dataBinding"), dict)
                        and block.get("dataBinding", {}).get("operationId")
                    )
                )
                if has_bind and cls.projection_is_empty(block):
                    issues.append(f"projection.empty:{block.get('id') or block.get('type')}")
        return issues
