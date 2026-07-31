from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tv_app.application.services.external_url_validator_service import validate_external_url
from tv_app.application.services.slide_template_mdd_service import (
    load_mdd_templates,
    resolve_mdd_template_bytes,
)
from tv_app.config import settings

PRESETS_PATH = Path(__file__).resolve().parents[2] / "content" / "dashboard_slide_presets.json"


class SlidePresetNotFoundError(LookupError):
    pass


@lru_cache(maxsize=1)
def _load_presets_file() -> dict[str, Any]:
    return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))


@lru_cache(maxsize=1)
def _load_mdd_templates_cached() -> tuple[dict[str, Any], ...]:
    return tuple(load_mdd_templates())


def clear_slide_preset_caches() -> None:
    """Invalida caches (útil em testes / regeneração de .mdd)."""
    _load_presets_file.cache_clear()
    _load_mdd_templates_cached.cache_clear()


def _json_presets() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _load_presets_file().get("presets") or []:
        if not isinstance(raw, dict) or not raw.get("key"):
            continue
        items.append(raw)
    return items


def _mdd_presets() -> list[dict[str, Any]]:
    return [dict(item) for item in _load_mdd_templates_cached()]


def _merged_presets_by_key() -> dict[str, dict[str, Any]]:
    """JSON legado + templates `.mdd` (MDD sobrescreve a mesma key)."""
    merged: dict[str, dict[str, Any]] = {}
    for raw in _json_presets():
        merged[str(raw["key"])] = raw
    for raw in _mdd_presets():
        merged[str(raw["key"])] = raw
    return merged


def list_slide_presets() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _merged_presets_by_key().values():
        items.append(
            {
                "key": raw["key"],
                "label": raw.get("label") or raw["key"],
                "description": raw.get("description"),
                "slideType": raw.get("slideType"),
                "durationSec": raw.get("durationSec"),
                "source": raw.get("source") or "json",
            }
        )
    items.sort(key=lambda item: str(item.get("label") or item.get("key") or ""))
    return items


def _public_origin() -> str:
    return (settings.PUBLIC_BASE_URL or "http://localhost").rstrip("/")


def resolve_preset_slide(preset_key: str) -> dict[str, Any]:
    raw = _merged_presets_by_key().get(preset_key)
    if not raw:
        raise SlidePresetNotFoundError(preset_key)
    slide_type = str(raw.get("slideType") or "").strip()
    title = str(raw.get("title") or raw.get("label") or "Tela importada").strip()
    duration = raw.get("durationSec")
    payload: dict[str, Any] = {
        "slideType": slide_type,
        "title": title,
        "durationSec": duration,
        "source": raw.get("source") or "json",
    }
    if slide_type == "native":
        payload["nativeScreenKey"] = raw.get("nativeScreenKey")
        payload["nativeConfig"] = dict(raw.get("nativeConfig") or {})
        return payload
    if slide_type == "external":
        url = raw.get("externalUrl")
        if not url and raw.get("externalUrlPath"):
            url = f"{_public_origin()}{str(raw['externalUrlPath']).strip()}"
        if not url:
            raise SlidePresetNotFoundError(f"Preset externo sem URL: {preset_key}")
        validate_external_url(str(url))
        payload["externalUrl"] = str(url).strip()
        return payload
    raise SlidePresetNotFoundError(f"Tipo de slide inválido no preset: {preset_key}")


def export_preset_mdd(preset_key: str) -> tuple[bytes, str]:
    """Bytes do `.mdd` catalogado (arquivo na pasta) ou reconstrói a partir do preset resolvido."""
    from tv_app.application.services.slide_template_mdd_service import build_slide_template_mdd

    existing = resolve_mdd_template_bytes(preset_key)
    if existing is not None:
        safe = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in preset_key)
        return existing, f"{safe}.mdd"

    detail = resolve_preset_slide(preset_key)
    if detail.get("slideType") != "native":
        raise SlidePresetNotFoundError(f"Preset não exportável como template MDD: {preset_key}")
    meta = _merged_presets_by_key().get(preset_key) or {}
    return build_slide_template_mdd(
        key=preset_key,
        label=str(meta.get("label") or detail.get("title") or preset_key),
        description=meta.get("description"),
        title=str(detail.get("title") or preset_key),
        duration_sec=detail.get("durationSec"),
        native_config=dict(detail.get("nativeConfig") or {}),
        native_screen_key=str(detail.get("nativeScreenKey") or "custom_message"),
    )
