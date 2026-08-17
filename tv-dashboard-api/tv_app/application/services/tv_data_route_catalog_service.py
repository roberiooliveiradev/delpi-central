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
# Grade (`canvas_table`): dataSourceId no bloco + dataRef por célula (≠ table_view).
CANVAS_TABLE_DATA_BOUND_BLOCK_TYPES = frozenset({"canvas_table"})
FETCHABLE_DATA_BLOCK_TYPES = DATA_BLOCK_TYPES

# Campos de overlay aplicados em runtime sem regenerar o catálogo completo.
# Labels/campos de valor: mesma fonte curada das rotas (overlay), para o picker
# de «Campo dinâmico» sem esperar sync OpenAPI.
# seriesField/tableFields: necessários para extrair pontos/linhas (senão a TV
# cai em total/granularity ou campo/valor).
_RUNTIME_OVERLAY_KEYS = frozenset(
    {
        "suggestedTransformSteps",
        "tvConstraints",
        "valueFields",
        "valueFieldLabels",
        "valueFieldTypes",
        "seriesField",
        "tableFields",
        "allowedDisplayModes",
        "label",
        "description",
        "whenToUse",
        "openEndedDateRange",
        "defaultParams",
        "exposesSiGoal",
    }
)

_DEFAULT_SI_GOAL_FIELD_LABELS: dict[str, str] = {
    "comparable_goal": "Meta do período",
    "goal_value": "Meta cadastrada",
    "reference_goal": "Meta mês (referência)",
}


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
def _load_overlays_document() -> dict[str, Any]:
    if not OVERLAYS_PATH.is_file():
        return {}
    payload = json.loads(OVERLAYS_PATH.read_text(encoding="utf-8"))
    return payload if isinstance(payload, dict) else {}


@lru_cache(maxsize=1)
def _load_overlays() -> dict[str, dict[str, Any]]:
    payload = _load_overlays_document()
    raw = payload.get("overlays")
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): dict(value)
        for key, value in raw.items()
        if isinstance(value, dict)
    }


@lru_cache(maxsize=1)
def _si_goal_field_labels() -> dict[str, str]:
    """Rótulos canônicos de meta SI para o picker (cadastrada / período / referência)."""
    payload = _load_overlays_document()
    raw = payload.get("siGoalFieldLabels")
    if isinstance(raw, dict) and raw:
        out: dict[str, str] = {}
        for key, label in raw.items():
            field = str(key or "").strip()
            text = str(label or "").strip()
            if field and text:
                out[field] = text
        if out:
            return out
    return dict(_DEFAULT_SI_GOAL_FIELD_LABELS)


@lru_cache(maxsize=1)
def _load_operation_id_aliases() -> dict[str, str]:
    if not ALIASES_PATH.is_file():
        return {}
    payload = json.loads(ALIASES_PATH.read_text(encoding="utf-8"))
    raw = payload.get("aliases") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    return {
        str(key): str(value)
        for key, value in raw.items()
        if str(key).strip() and str(value).strip()
    }


def resolve_canonical_operation_id(operation_id: str | None) -> str:
    op = str(operation_id or "").strip()
    if not op:
        return ""
    return _load_operation_id_aliases().get(op, op)


def _apply_si_goal_picker_fields(route: dict[str, Any], *, overlay: dict[str, Any]) -> dict[str, Any]:
    """Garante tríade de meta SI no picker de hubs com enriquecimento SI.

    Sem isso, o campo só aparece via discovery quando o preview já trouxe valor —
    e some do «Campo dinâmico» se a meta estiver vazia ou o resolved falhar.
    """
    exposes = bool(overlay.get("exposesSiGoal"))
    labels = route.get("valueFieldLabels") if isinstance(route.get("valueFieldLabels"), dict) else {}
    if not exposes and not any(field in labels for field in _si_goal_field_labels()):
        return route

    merged = dict(route)
    next_labels = dict(labels)
    for field, label in _si_goal_field_labels().items():
        next_labels[field] = label
    merged["valueFieldLabels"] = next_labels

    fields = [
        str(item).strip()
        for item in (merged.get("valueFields") or [])
        if str(item).strip()
    ]
    for field in _si_goal_field_labels():
        if field not in fields:
            fields.append(field)
    if fields:
        merged["valueFields"] = fields
    return merged


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
    if merged.get("openEndedDateRange"):
        defaults = merged.get("defaultParams")
        if isinstance(defaults, dict) and "periodDays" in defaults:
            cleaned = {k: v for k, v in defaults.items() if k != "periodDays"}
            if cleaned:
                merged["defaultParams"] = cleaned
            else:
                merged.pop("defaultParams", None)
    merged = _apply_si_goal_picker_fields(merged, overlay=overlay)
    # Flag só de overlay — não precisa ir ao cliente.
    merged.pop("exposesSiGoal", None)
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
    _load_overlays_document.cache_clear()
    _load_overlays.cache_clear()
    _si_goal_field_labels.cache_clear()
    _load_operation_id_aliases.cache_clear()
