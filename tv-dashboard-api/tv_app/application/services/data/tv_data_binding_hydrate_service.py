"""Hydrate dataBindings contra o catálogo vivo (labels, aliases de data, strip de params)."""

from __future__ import annotations

from typing import Any

from tv_app.application.services.data.tv_data_param_defaults_service import (
    apply_catalog_param_defaults,
)
from tv_app.application.services.tv_data_route_catalog_service import (
    DATA_BLOCK_TYPES,
    TvDataRouteCatalogService,
)
from tv_app.application.services.tv_date_range_preset_service import (
    DATE_RANGE_PRESET_KEY,
    INTERNAL_PARAM_KEYS,
    PERIOD_DAYS_KEY,
)

# Legado → canônico HTTP (schema preferindo start_date/end_date).
_PARAM_KEY_REMAP: dict[str, str] = {
    "date_start": "start_date",
    "date_end": "end_date",
    "dataInicio": "start_date",
    "dataFim": "end_date",
    "data_inicio": "start_date",
    "data_fim": "end_date",
    "data_inicial": "start_date",
    "data_final": "end_date",
    "date_from": "start_date",
    "date_to": "end_date",
}

_KEEP_WITHOUT_SCHEMA = frozenset({DATE_RANGE_PRESET_KEY, PERIOD_DAYS_KEY}) | INTERNAL_PARAM_KEYS


def _is_catalog_like_label(label: Any, route: dict[str, Any] | None) -> bool:
    trimmed = str(label or "").strip()
    if not trimmed:
        return True
    if not isinstance(route, dict):
        return False
    current = str(route.get("label") or "").strip()
    if current and trimmed == current:
        return True
    aliases = route.get("labelAliases")
    if not isinstance(aliases, list):
        return False
    return any(str(alias or "").strip() == trimmed for alias in aliases)


def _remap_param_keys(
    params: dict[str, Any],
    schema_keys: set[str],
) -> tuple[dict[str, Any], list[str]]:
    out = dict(params)
    remapped: list[str] = []
    for legacy, canonical in _PARAM_KEY_REMAP.items():
        if legacy not in out:
            continue
        # Se o schema ainda expõe só a chave legada, não remapeia.
        if schema_keys and canonical not in schema_keys and legacy in schema_keys:
            continue
        value = out.pop(legacy)
        remapped.append(f"{legacy}→{canonical}")
        if value in (None, ""):
            continue
        if out.get(canonical) in (None, ""):
            out[canonical] = value
    return out, remapped


def _strip_unknown_params(
    params: dict[str, Any],
    *,
    schema_keys: set[str],
    fixed_keys: set[str],
) -> tuple[dict[str, Any], list[str]]:
    if not schema_keys:
        # Sem schema: só remove vazios; mantém o restante.
        return (
            {k: v for k, v in params.items() if v not in (None, "")},
            [],
        )
    stripped: list[str] = []
    kept: dict[str, Any] = {}
    for key, value in params.items():
        if value in (None, ""):
            continue
        if key in fixed_keys:
            continue
        if key in _KEEP_WITHOUT_SCHEMA or key in schema_keys:
            kept[key] = value
            continue
        stripped.append(key)
    return kept, stripped


def hydrate_data_binding(
    binding: dict[str, Any],
    route: dict[str, Any] | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Retorna (binding_hydrated, diagnostics)."""
    diagnostics: dict[str, Any] = {
        "orphan": False,
        "strippedParams": [],
        "remappedParams": [],
        "clearedLabel": False,
    }
    next_binding = dict(binding)
    operation_id = str(binding.get("operationId") or "").strip()
    if operation_id and route is None:
        diagnostics["orphan"] = True

    if _is_catalog_like_label(binding.get("label"), route):
        if binding.get("label") not in (None, ""):
            next_binding.pop("label", None)
            diagnostics["clearedLabel"] = True

    raw_params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
    schema = route.get("paramSchema") if isinstance(route, dict) else None
    schema = schema if isinstance(schema, dict) else {}
    schema_keys = set(schema.keys())
    fixed = route.get("fixedQueryParams") if isinstance(route, dict) else None
    fixed_keys = set(fixed.keys()) if isinstance(fixed, dict) else set()

    remapped_params, remapped = _remap_param_keys(dict(raw_params), schema_keys)
    diagnostics["remappedParams"] = remapped
    stripped_params, stripped = _strip_unknown_params(
        remapped_params,
        schema_keys=schema_keys,
        fixed_keys=fixed_keys,
    )
    diagnostics["strippedParams"] = stripped

    if isinstance(route, dict):
        stripped_params = apply_catalog_param_defaults(stripped_params, route)

    next_binding["params"] = stripped_params
    return next_binding, diagnostics


def hydrate_comunicado_data_bindings(
    cfg: dict[str, Any],
    *,
    catalog: TvDataRouteCatalogService | None = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    """Hydrate todos os dataBindings + dataFilters. Retorna (cfg, summary)."""
    cat = catalog or TvDataRouteCatalogService()
    if not isinstance(cfg, dict):
        return {}, {"orphanOperationIds": [], "strippedParams": [], "remappedParams": [], "clearedLabels": 0}

    result = dict(cfg)
    blocks_in = result.get("blocks")
    orphan_ids: list[str] = []
    stripped_all: list[str] = []
    remapped_all: list[str] = []
    cleared_labels = 0

    if isinstance(blocks_in, list):
        next_blocks: list[Any] = []
        for block in blocks_in:
            if not isinstance(block, dict):
                next_blocks.append(block)
                continue
            block_type = str(block.get("type") or "")
            binding = block.get("dataBinding")
            if block_type not in DATA_BLOCK_TYPES or not isinstance(binding, dict):
                next_blocks.append(block)
                continue
            operation_id = str(binding.get("operationId") or "").strip()
            route = cat.get_route(operation_id) if operation_id else None
            hydrated, diag = hydrate_data_binding(binding, route)
            if diag.get("orphan") and operation_id:
                orphan_ids.append(operation_id)
            stripped_all.extend(diag.get("strippedParams") or [])
            remapped_all.extend(diag.get("remappedParams") or [])
            if diag.get("clearedLabel"):
                cleared_labels += 1
            next_block = dict(block)
            next_block["dataBinding"] = hydrated
            next_blocks.append(next_block)
        result["blocks"] = next_blocks

    filters = result.get("dataFilters")
    if isinstance(filters, dict) and filters:
        # União de schemas das rotas do slide para strip conservador.
        union_schema: dict[str, Any] = {}
        for block in result.get("blocks") or []:
            if not isinstance(block, dict):
                continue
            binding = block.get("dataBinding")
            if not isinstance(binding, dict):
                continue
            op = str(binding.get("operationId") or "").strip()
            route = cat.get_route(op) if op else None
            schema = route.get("paramSchema") if isinstance(route, dict) else None
            if isinstance(schema, dict):
                union_schema.update(schema)
        fake_route = {"paramSchema": union_schema, "defaultParams": {}}
        hydrated_filters, diag = hydrate_data_binding(
            {"operationId": "", "params": filters},
            fake_route,
        )
        params = hydrated_filters.get("params")
        result["dataFilters"] = params if isinstance(params, dict) and params else None
        stripped_all.extend(diag.get("strippedParams") or [])
        remapped_all.extend(diag.get("remappedParams") or [])

    summary = {
        "orphanOperationIds": sorted(set(orphan_ids)),
        "strippedParams": sorted(set(stripped_all)),
        "remappedParams": sorted(set(remapped_all)),
        "clearedLabels": cleared_labels,
    }
    return result, summary
