"""Parse e allowlist de overrides de filtro do present público (sessão kiosk)."""

from __future__ import annotations

import json
from typing import Any


def parse_filter_overrides_query(
    filters_json: str | None,
    extra_df_params: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """
    Aceita `filters` JSON: { slide?: {}, bySourceId?: { id: {} } }
    e/ou params `df.<key>` → slide[key].
    """
    slide: dict[str, Any] = {}
    by_source: dict[str, dict[str, Any]] = {}

    if filters_json and str(filters_json).strip():
        try:
            raw = json.loads(filters_json)
        except json.JSONDecodeError:
            raw = None
        if isinstance(raw, dict):
            if isinstance(raw.get("slide"), dict):
                slide.update({str(k): v for k, v in raw["slide"].items()})
            if isinstance(raw.get("bySourceId"), dict):
                for sid, params in raw["bySourceId"].items():
                    if isinstance(params, dict):
                        by_source[str(sid)] = {str(k): v for k, v in params.items()}
            # Atalho: mapa flat no root = slide
            for key, value in raw.items():
                if key in {"slide", "bySourceId"}:
                    continue
                if value is not None and value != "" and not isinstance(value, dict):
                    slide[str(key)] = value

    if extra_df_params:
        for key, value in extra_df_params.items():
            if value is not None and value != "":
                slide[str(key)] = value

    if not slide and not by_source:
        return None
    return {"slide": slide, "bySourceId": by_source}


def allowlist_filter_overrides(
    overrides: dict[str, Any] | None,
    *,
    allowed_slide_keys: set[str],
    allowed_by_source: dict[str, set[str]],
) -> dict[str, Any] | None:
    """Mantém só keys/sourceIds declarados por blocos input da programação."""
    if not isinstance(overrides, dict):
        return None
    slide_in = overrides.get("slide") if isinstance(overrides.get("slide"), dict) else {}
    by_in = overrides.get("bySourceId") if isinstance(overrides.get("bySourceId"), dict) else {}

    slide = {k: v for k, v in slide_in.items() if str(k) in allowed_slide_keys and v not in (None, "")}
    by_source: dict[str, dict[str, Any]] = {}
    for sid, params in by_in.items():
        if not isinstance(params, dict):
            continue
        allowed_keys = allowed_by_source.get(str(sid)) or set()
        filtered = {
            str(k): v
            for k, v in params.items()
            if str(k) in allowed_keys and v not in (None, "")
        }
        if filtered:
            by_source[str(sid)] = filtered

    if not slide and not by_source:
        return None
    return {"slide": slide, "bySourceId": by_source}


def collect_allowed_input_keys_from_playlist_slides(
    slides: list[dict[str, Any]],
) -> tuple[set[str], dict[str, set[str]]]:
    """Varre nativeConfig.blocks dos slides custom_message."""
    slide_keys: set[str] = set()
    by_source: dict[str, set[str]] = {}
    for slide in slides:
        if slide.get("slideType") != "native":
            continue
        if str(slide.get("nativeScreenKey") or "") != "custom_message":
            continue
        cfg = slide.get("nativeConfig") if isinstance(slide.get("nativeConfig"), dict) else {}
        blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
        for block in blocks:
            if not isinstance(block, dict) or str(block.get("type") or "") != "input":
                continue
            input_cfg = block.get("input") if isinstance(block.get("input"), dict) else {}
            param_key = str(input_cfg.get("paramKey") or "").strip()
            if not param_key:
                continue
            scope = "sources" if input_cfg.get("targetScope") == "sources" else "slide"
            if scope == "slide":
                slide_keys.add(param_key)
            else:
                for sid in input_cfg.get("targetSourceIds") or []:
                    source_id = str(sid).strip()
                    if not source_id:
                        continue
                    by_source.setdefault(source_id, set()).add(param_key)
    return slide_keys, by_source
