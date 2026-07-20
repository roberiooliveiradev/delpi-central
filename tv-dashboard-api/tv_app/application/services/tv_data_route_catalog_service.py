from __future__ import annotations

import json
import os
from functools import lru_cache
from pathlib import Path
from typing import Any

_PACKAGED_ROUTES = Path(__file__).resolve().parents[2] / "content" / "tv_data_routes.json"
OVERLAYS_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_data_route_overlays.json"
ALIASES_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_operation_id_aliases.json"


def resolve_routes_path() -> Path:
    """Path do catálogo: volume persistente (env) ou artefato empacotado."""
    raw = str(os.getenv("TV_DATA_ROUTES_PATH") or "").strip()
    if raw:
        return Path(raw)
    return _PACKAGED_ROUTES


ROUTES_PATH = resolve_routes_path()

DATA_BLOCK_TYPES = frozenset({"data_kpi", "data_chart", "data_table", "data_metric", "data_source"})
DATA_VIEW_BLOCK_TYPES = frozenset({"chart_view", "table_view", "kpi_view"})
TEXT_DATA_BOUND_BLOCK_TYPES = frozenset({"heading", "text", "shape"})
FETCHABLE_DATA_BLOCK_TYPES = DATA_BLOCK_TYPES

# Campos de overlay aplicados em runtime sem regenerar o catálogo completo.
_RUNTIME_OVERLAY_KEYS = frozenset({"suggestedTransformSteps", "tvConstraints"})


@lru_cache(maxsize=1)
def _load_catalog() -> dict[str, Any]:
    path = resolve_routes_path()
    if path.is_file():
        return json.loads(path.read_text(encoding="utf-8"))
    # Fallback: catálogo empacotado na imagem (antes do 1º sync no volume).
    if _PACKAGED_ROUTES.is_file() and path != _PACKAGED_ROUTES:
        return json.loads(_PACKAGED_ROUTES.read_text(encoding="utf-8"))
    raise FileNotFoundError(f"Catálogo TV ausente: {path}")


@lru_cache(maxsize=1)
def _load_overlays() -> dict[str, dict[str, Any]]:
    if not OVERLAYS_PATH.is_file():
        return {}
    payload = json.loads(OVERLAYS_PATH.read_text(encoding="utf-8"))
    raw = payload.get("overlays") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict)
    }


@lru_cache(maxsize=1)
def _load_operation_id_aliases() -> dict[str, str]:
    """Mapa legado → canônico (playlists salvas com operationId auto-FastAPI)."""
    if not ALIASES_PATH.is_file():
        return {}
    payload = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    raw = payload.get("aliases") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(legacy).strip(): str(canonical).strip()
        for legacy, canonical in raw.items()
        if str(legacy).strip() and str(canonical).strip()
    }


def resolve_canonical_operation_id(operation_id: str) -> str:
    op = str(operation_id or "").strip()
    if not op:
        return ""
    return _load_operation_id_aliases().get(op, op)


def _merge_runtime_overlay(route: dict[str, Any]) -> dict[str, Any]:
    operation_id = str(route.get("operationId") or "").strip()
    overlay = _load_overlays().get(operation_id)
    if not overlay:
        return route
    merged = dict(route)
    for key in _RUNTIME_OVERLAY_KEYS:
        if key in overlay:
            if isinstance(overlay[key], dict) and isinstance(merged.get(key), dict):
                merged[key] = {**merged[key], **overlay[key]}
            else:
                merged[key] = overlay[key]
    return merged


class TvDataRouteCatalogService:
    """Allowlist de rotas api-delpi disponíveis para blocos data_* na TV."""

    def list_routes(self) -> list[dict[str, Any]]:
        raw = _load_catalog().get("routes") or []
        if not isinstance(raw, list):
            return []
        return [
            _merge_runtime_overlay(dict(item))
            for item in raw
            if isinstance(item, dict)
        ]

    def get_route(self, operation_id: str) -> dict[str, Any] | None:
        op = resolve_canonical_operation_id(operation_id)
        if not op:
            return None
        for route in self.list_routes():
            if str(route.get("operationId") or "") == op:
                return route
        return None

    def is_allowed(self, operation_id: str) -> bool:
        return self.get_route(operation_id) is not None

    @staticmethod
    def is_data_block(block: dict[str, Any]) -> bool:
        return str(block.get("type") or "") in DATA_BLOCK_TYPES

    @staticmethod
    def is_data_view_block(block: dict[str, Any]) -> bool:
        return str(block.get("type") or "") in DATA_VIEW_BLOCK_TYPES


def normalize_data_binding_operation_id(binding: dict[str, Any] | None) -> dict[str, Any] | None:
    """Reescreve operationId legado → canônico no dataBinding (UI / persistência)."""
    if not isinstance(binding, dict):
        return binding
    raw = str(binding.get("operationId") or "").strip()
    canonical = resolve_canonical_operation_id(raw)
    if not canonical or canonical == raw:
        return binding
    return {**binding, "operationId": canonical}


def reset_tv_data_route_catalog_cache() -> None:
    _load_catalog.cache_clear()
    _load_overlays.cache_clear()
    _load_operation_id_aliases.cache_clear()
