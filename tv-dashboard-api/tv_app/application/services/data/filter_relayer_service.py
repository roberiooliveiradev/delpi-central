"""Promote shared data_source params to playlist/slide filter layers."""

from __future__ import annotations

from typing import Any, Mapping

from tv_app.application.services.comunicado_data_params_service import (
    BRANCH_PARAM_KEYS,
    resolve_any_branch_value,
)
from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    PERIOD_DAYS_KEY,
    merge_period_params_layer,
)

_PROMOTE_KEYS = frozenset(
    {
        "branch",
        "filial",
        "branch_code",
        "filial_id",
        DATE_RANGE_PRESET_KEY,
        PERIOD_DAYS_KEY,
        "competence",
    }
)


def _param_value(params: Mapping[str, Any], key: str) -> Any:
    if key in BRANCH_PARAM_KEYS:
        return resolve_any_branch_value(params)
    return params.get(key)


def shared_keys_across_sources(
    native_config: Mapping[str, Any],
    *,
    keys: list[str] | None = None,
) -> dict[str, Any]:
    """Return keys whose normalized value is identical on all data_source blocks."""
    blocks = native_config.get("blocks") if isinstance(native_config.get("blocks"), list) else []
    sources: list[dict[str, Any]] = []
    for block in blocks:
        if not isinstance(block, dict) or str(block.get("type") or "") != "data_source":
            continue
        binding = block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
        params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
        sources.append({"blockId": str(block.get("id") or ""), "params": dict(params)})
    if len(sources) < 1:
        return {}
    allowed = {str(k) for k in (keys or []) if str(k).strip()} or set(_PROMOTE_KEYS)
    promoted: dict[str, Any] = {}
    for key in allowed:
        values: list[Any] = []
        for src in sources:
            params = src["params"]
            val = _param_value(params, key)
            if val is None or val == "":
                values.append(None)
            else:
                values.append(val)
        non_empty = [v for v in values if v not in (None, "")]
        if len(non_empty) != len(sources):
            continue
        if len({str(v) for v in non_empty}) == 1:
            wire_key = "branch" if key in BRANCH_PARAM_KEYS else key
            promoted[wire_key] = non_empty[0]
    return promoted


def apply_relayer(
    native_config: dict[str, Any],
    *,
    scope: str,
    keys: list[str] | None,
    playlist_defaults: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any] | None, dict[str, Any]]:
    """Mutate native_config in place. Returns (native, playlist_defaults, promoted)."""
    scope_s = str(scope or "slide").strip().lower()
    if scope_s not in {"playlist", "slide"}:
        raise ValueError("scope must be playlist or slide")
    promoted = shared_keys_across_sources(native_config, keys=keys)
    if not promoted:
        return native_config, playlist_defaults, promoted

    defaults = dict(playlist_defaults) if isinstance(playlist_defaults, dict) else {}
    if scope_s == "playlist":
        defaults = merge_period_params_layer(defaults, promoted)
        playlist_defaults = defaults
    else:
        filters = native_config.get("dataFilters")
        merged = dict(filters) if isinstance(filters, dict) else {}
        native_config["dataFilters"] = merge_period_params_layer(merged, promoted)

    blocks = native_config.get("blocks")
    if isinstance(blocks, list):
        for block in blocks:
            if not isinstance(block, dict) or str(block.get("type") or "") != "data_source":
                continue
            binding = block.get("dataBinding")
            if not isinstance(binding, dict):
                continue
            params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
            next_params = dict(params)
            for key in list(promoted.keys()):
                for alias in (key, *BRANCH_PARAM_KEYS):
                    next_params.pop(alias, None)
            binding["params"] = next_params
            block.pop("resolved", None)

    return native_config, playlist_defaults, promoted
