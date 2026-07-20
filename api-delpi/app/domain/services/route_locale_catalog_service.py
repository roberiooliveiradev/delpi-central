"""Catálogo de locale bilíngue (EN / pt-BR) por operationId + params globais."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_DIR = Path(__file__).resolve().parents[2] / "content"
_AUDIENCE_PATH = _CONTENT_DIR / "tv_route_audience.json"
_PARAM_LOCALE_PATH = _CONTENT_DIR / "openapi_param_locale.json"

_LOCALE_KEYS = ("summary", "description", "whenToUse", "label")


def _clean_locale_block(raw: Any) -> dict[str, str]:
    if not isinstance(raw, dict):
        return {}
    cleaned: dict[str, str] = {}
    for key in _LOCALE_KEYS:
        value = str(raw.get(key) or "").strip()
        if value:
            cleaned[key] = value
    return cleaned


def _clean_params(raw: Any) -> dict[str, dict[str, Any]]:
    if not isinstance(raw, dict):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for name, value in raw.items():
        key = str(name or "").strip()
        if not key or not isinstance(value, dict):
            continue
        locale_raw = value.get("locale") if isinstance(value.get("locale"), dict) else {}
        locale: dict[str, dict[str, str]] = {}
        for lang in ("en", "pt-BR"):
            block = _clean_locale_block(locale_raw.get(lang))
            if block:
                locale[lang] = block
        if locale:
            indexed[key] = {"locale": locale}
    return indexed


def _normalize_route_entry(value: dict[str, Any]) -> dict[str, Any]:
    """Aceita v2 (locale) e v1 legado (whenToUse/description no root → pt-BR)."""
    cleaned: dict[str, Any] = {}
    category = str(value.get("category") or "").strip()
    if category:
        cleaned["category"] = category

    locale_raw = value.get("locale") if isinstance(value.get("locale"), dict) else {}
    locale: dict[str, dict[str, str]] = {}
    for lang in ("en", "pt-BR"):
        block = _clean_locale_block(locale_raw.get(lang))
        if block:
            locale[lang] = block

    legacy = _clean_locale_block(value)
    if legacy:
        pt = dict(locale.get("pt-BR") or {})
        for key, text in legacy.items():
            pt.setdefault(key, text)
        locale["pt-BR"] = pt

    if locale:
        cleaned["locale"] = locale

    params = _clean_params(value.get("params"))
    if params:
        cleaned["params"] = params

    return cleaned


@lru_cache(maxsize=1)
def _load_audience_routes() -> dict[str, dict[str, Any]]:
    if not _AUDIENCE_PATH.is_file():
        return {}
    payload = json.loads(_AUDIENCE_PATH.read_text(encoding="utf-8"))
    raw = payload.get("routes") if isinstance(payload, dict) else None
    if not isinstance(raw, dict):
        return {}
    indexed: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        op = str(key or "").strip()
        if not op or not isinstance(value, dict):
            continue
        cleaned = _normalize_route_entry(value)
        if cleaned:
            indexed[op] = cleaned
    return indexed


@lru_cache(maxsize=1)
def load_global_param_locale() -> dict[str, dict[str, Any]]:
    """Params compartilhados (branch, periodDays, …) — openapi_param_locale.json."""
    if not _PARAM_LOCALE_PATH.is_file():
        return {}
    payload = json.loads(_PARAM_LOCALE_PATH.read_text(encoding="utf-8"))
    return _clean_params(payload.get("params") if isinstance(payload, dict) else None)


def route_locale_for_operation(operation_id: str) -> dict[str, Any] | None:
    """Retorna { category?, locale?, params? } curados para o operationId."""
    op = str(operation_id or "").strip()
    if not op:
        return None
    entry = _load_audience_routes().get(op)
    return dict(entry) if entry else None


def tv_audience_for_operation(operation_id: str) -> dict[str, Any] | None:
    """Compat: audiência TV a partir de locale.pt-BR (whenToUse / description / label)."""
    entry = route_locale_for_operation(operation_id)
    if not entry:
        return None
    locale = entry.get("locale") if isinstance(entry.get("locale"), dict) else {}
    pt = locale.get("pt-BR") if isinstance(locale.get("pt-BR"), dict) else {}
    cleaned: dict[str, Any] = {}
    for key in ("whenToUse", "description", "label"):
        value = str(pt.get(key) or "").strip()
        if value:
            cleaned[key] = value
    if "label" not in cleaned:
        summary = str(pt.get("summary") or "").strip()
        if summary:
            cleaned["label"] = summary
    return cleaned or None


def _merge_param_locale(
    base: dict[str, dict[str, Any]] | None,
    overlay: dict[str, dict[str, Any]] | None,
) -> dict[str, dict[str, Any]]:
    merged = {k: dict(v) for k, v in (base or {}).items()}
    for name, value in (overlay or {}).items():
        if name not in merged:
            merged[name] = dict(value)
            continue
        left = merged[name]
        right_locale = value.get("locale") if isinstance(value.get("locale"), dict) else {}
        left_locale = left.get("locale") if isinstance(left.get("locale"), dict) else {}
        combined: dict[str, dict[str, str]] = {**left_locale}
        for lang, block in right_locale.items():
            if not isinstance(block, dict):
                continue
            combined[lang] = {**(combined.get(lang) or {}), **block}
        left["locale"] = combined
        merged[name] = left
    return merged


def apply_route_locale_to_x_delpi(
    extension: dict[str, Any],
    operation_id: str,
    *,
    param_names: set[str] | frozenset[str] | None = None,
) -> dict[str, Any]:
    """Mescla locale/params/category curados + params globais da rota; espelha tv a partir de pt-BR.

    Quando ``param_names`` é informado, só anexa locale global para esses nomes
    (evita dump de todo ``openapi_param_locale.json`` em cada operação).
    """
    merged = dict(extension)
    entry = route_locale_for_operation(operation_id) or {}
    category = str(entry.get("category") or "").strip()
    if category:
        merged["category"] = category
    locale = entry.get("locale")
    if isinstance(locale, dict) and locale:
        merged["locale"] = locale
    route_params = entry.get("params") if isinstance(entry.get("params"), dict) else {}
    global_params = load_global_param_locale()
    if param_names is not None:
        allowed = {str(n).strip() for n in param_names if str(n).strip()}
        global_params = {k: v for k, v in global_params.items() if k in allowed}
        route_params = {k: v for k, v in route_params.items() if k in allowed}
    params = _merge_param_locale(global_params, route_params)
    existing = merged.get("params") if isinstance(merged.get("params"), dict) else {}
    if param_names is not None:
        allowed = {str(n).strip() for n in param_names if str(n).strip()}
        existing = {k: v for k, v in _clean_params(existing).items() if k in allowed}
        merged_params = _merge_param_locale(params, existing)
        if merged_params:
            merged["params"] = merged_params
        else:
            merged.pop("params", None)
    elif params:
        merged["params"] = _merge_param_locale(params, _clean_params(existing))
    tv = tv_audience_for_operation(operation_id)
    if tv:
        merged["tv"] = tv
    return merged


def reset_route_locale_catalog_cache() -> None:
    _load_audience_routes.cache_clear()
    load_global_param_locale.cache_clear()
