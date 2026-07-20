"""Catálogo de locale bilíngue (EN / pt-BR) por operationId — fonte curada em JSON."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

_CONTENT_PATH = Path(__file__).resolve().parents[2] / "content" / "tv_route_audience.json"

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

    # Compat v1: campos no root viram pt-BR.
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
    if not _CONTENT_PATH.is_file():
        return {}
    payload = json.loads(_CONTENT_PATH.read_text(encoding="utf-8"))
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


def apply_route_locale_to_x_delpi(
    extension: dict[str, Any],
    operation_id: str,
) -> dict[str, Any]:
    """Mescla locale/params/category curados em x-delpi; espelha tv a partir de pt-BR."""
    entry = route_locale_for_operation(operation_id)
    if not entry:
        return extension
    merged = dict(extension)
    category = str(entry.get("category") or "").strip()
    if category:
        merged["category"] = category
    locale = entry.get("locale")
    if isinstance(locale, dict) and locale:
        merged["locale"] = locale
    params = entry.get("params")
    if isinstance(params, dict) and params:
        merged["params"] = params
    tv = tv_audience_for_operation(operation_id)
    if tv:
        merged["tv"] = tv
    return merged


def reset_route_locale_catalog_cache() -> None:
    _load_audience_routes.cache_clear()
