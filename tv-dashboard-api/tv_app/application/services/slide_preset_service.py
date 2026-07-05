from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Any

from tv_app.application.services.external_url_validator_service import validate_external_url
from tv_app.config import settings

PRESETS_PATH = Path(__file__).resolve().parents[2] / "content" / "dashboard_slide_presets.json"


class SlidePresetNotFoundError(LookupError):
    pass


@lru_cache(maxsize=1)
def _load_presets_file() -> dict[str, Any]:
    return json.loads(PRESETS_PATH.read_text(encoding="utf-8"))


def list_slide_presets() -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for raw in _load_presets_file().get("presets") or []:
        if not isinstance(raw, dict) or not raw.get("key"):
            continue
        items.append(
            {
                "key": raw["key"],
                "label": raw.get("label") or raw["key"],
                "description": raw.get("description"),
                "slideType": raw.get("slideType"),
                "durationSec": raw.get("durationSec"),
            }
        )
    return items


def _public_origin() -> str:
    return (settings.PUBLIC_BASE_URL or "http://localhost").rstrip("/")


def resolve_preset_slide(preset_key: str) -> dict[str, Any]:
    for raw in _load_presets_file().get("presets") or []:
        if not isinstance(raw, dict) or raw.get("key") != preset_key:
            continue
        slide_type = str(raw.get("slideType") or "").strip()
        title = str(raw.get("title") or raw.get("label") or "Tela importada").strip()
        duration = raw.get("durationSec")
        payload: dict[str, Any] = {
            "slideType": slide_type,
            "title": title,
            "durationSec": duration,
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
    raise SlidePresetNotFoundError(preset_key)
