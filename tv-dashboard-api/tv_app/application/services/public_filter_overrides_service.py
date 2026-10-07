"""Parse e allowlist de overrides de filtro do present público (sessão kiosk)."""

from __future__ import annotations

import json
from typing import Any

from tv_app.application.services.comunicado_input_contract_service import (
    SLIDE_INPUT_OVERRIDES_KEY,
    is_variable_input,
)

BY_SLIDE_ID_KEY = "bySlideId"
_MAX_OVERRIDE_SLIDES = 200
_MAX_OVERRIDE_INPUTS_PER_SLIDE = 64
_SCALAR_OVERRIDE_TYPES = (str, int, float, bool)


def _is_scalar_override(value: Any) -> bool:
    """Override vindo do browser é sempre escalar — AST/objeto/lista é descartado."""
    return value is None or isinstance(value, _SCALAR_OVERRIDE_TYPES)


def _scalar_params(raw: dict[Any, Any]) -> dict[str, Any]:
    return {str(key): value for key, value in raw.items() if _is_scalar_override(value)}


def _parse_by_slide_id(raw: Any) -> dict[str, dict[str, Any]]:
    """{ slideId: { byInputId: { inputBlockId: escalar|null } } } — só forma, sem confiar em tipo."""
    out: dict[str, dict[str, Any]] = {}
    if not isinstance(raw, dict):
        return out
    for slide_id, bucket in list(raw.items())[:_MAX_OVERRIDE_SLIDES]:
        by_input = bucket.get(SLIDE_INPUT_OVERRIDES_KEY) if isinstance(bucket, dict) else None
        if not isinstance(by_input, dict):
            continue
        values = {
            str(input_id): value
            for input_id, value in list(by_input.items())[:_MAX_OVERRIDE_INPUTS_PER_SLIDE]
            if _is_scalar_override(value)
        }
        if values:
            out[str(slide_id)] = values
    return out


def parse_filter_overrides_query(
    filters_json: str | None,
    extra_df_params: dict[str, str] | None = None,
) -> dict[str, Any] | None:
    """
    Aceita `filters` JSON: { slide?: {}, bySourceId?: { id: {} },
    bySlideId?: { slideId: { byInputId: { inputBlockId: valor } } } }
    e/ou params `df.<key>` → slide[key]. ``bySlideId`` só alimenta inputs
    ``variable`` do próprio slide (``slide_input_overrides``).
    """
    slide: dict[str, Any] = {}
    by_source: dict[str, dict[str, Any]] = {}
    by_slide: dict[str, dict[str, Any]] = {}

    if filters_json and str(filters_json).strip():
        try:
            raw = json.loads(filters_json)
        except json.JSONDecodeError:
            raw = None
        if isinstance(raw, dict):
            if isinstance(raw.get("slide"), dict):
                slide.update(_scalar_params(raw["slide"]))
            if isinstance(raw.get("bySourceId"), dict):
                for sid, params in raw["bySourceId"].items():
                    if isinstance(params, dict):
                        by_source[str(sid)] = _scalar_params(params)
            by_slide = _parse_by_slide_id(raw.get(BY_SLIDE_ID_KEY))
            # Atalho: mapa flat no root = slide
            for key, value in raw.items():
                if key in {"slide", "bySourceId", BY_SLIDE_ID_KEY}:
                    continue
                if value is not None and value != "" and _is_scalar_override(value):
                    slide[str(key)] = value

    if extra_df_params:
        for key, value in extra_df_params.items():
            if value is not None and value != "" and _is_scalar_override(value):
                slide[str(key)] = value

    if not slide and not by_source and not by_slide:
        return None
    result: dict[str, Any] = {"slide": slide, "bySourceId": by_source}
    if by_slide:
        result[BY_SLIDE_ID_KEY] = by_slide
    return result


def slide_input_overrides(
    overrides: dict[str, Any] | None,
    *,
    slide_id: str,
    slide_blocks: list[Any],
) -> dict[str, Any]:
    """Fatia ``bySlideId[slide_id]`` restrita a inputs ``variable`` DESTE slide.

    O valor é validado depois contra o valueSchema persistido
    (``build_input_variable_scope``); id de outro slide/bloco não-input é descartado.
    """
    if not isinstance(overrides, dict):
        return {}
    by_slide = overrides.get(BY_SLIDE_ID_KEY)
    bucket = by_slide.get(str(slide_id)) if isinstance(by_slide, dict) else None
    if not isinstance(bucket, dict) or not bucket:
        return {}
    variable_ids = {
        str(block.get("id") or "")
        for block in slide_blocks
        if isinstance(block, dict)
        and str(block.get("type") or "") == "input"
        and is_variable_input(block.get("input"))
    }
    return {input_id: value for input_id, value in bucket.items() if input_id in variable_ids}


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
