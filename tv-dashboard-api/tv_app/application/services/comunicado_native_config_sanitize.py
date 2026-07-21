from __future__ import annotations

from typing import Any

from tv_app.application.services.data.data_transform_contract import (
    sanitize_data_transform_for_persistence,
)


def _strip_runtime_fields(block: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(block)
    cleaned.pop("resolved", None)
    cleaned.pop("url", None)
    if "dataTransform" in cleaned:
        transform = sanitize_data_transform_for_persistence(cleaned.get("dataTransform"))
        if transform is None:
            cleaned.pop("dataTransform", None)
        else:
            cleaned["dataTransform"] = transform
    return cleaned


def sanitize_comunicado_config(cfg: dict[str, Any] | None) -> dict[str, Any]:
    """Remove campos de runtime (resolved, url) antes de persistir native_config."""
    if not isinstance(cfg, dict):
        return {}
    result = dict(cfg)
    blocks_raw = result.get("blocks")
    if isinstance(blocks_raw, list):
        result["blocks"] = [
            _strip_runtime_fields(block) for block in blocks_raw if isinstance(block, dict)
        ]
    background = result.get("background")
    if isinstance(background, dict) and background.get("type") == "image":
        bg = dict(background)
        bg.pop("url", None)
        result["background"] = bg
    return result
