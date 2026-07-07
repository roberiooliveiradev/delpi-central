from __future__ import annotations

from typing import Any


def merge_data_params(
    *,
    playlist_defaults: dict[str, Any] | None,
    slide_filters: dict[str, Any] | None,
    block_params: dict[str, Any] | None,
) -> dict[str, Any]:
    """playlist → slide → bloco (mais específico ganha)."""
    merged: dict[str, Any] = {}
    for layer in (playlist_defaults, slide_filters, block_params):
        if not isinstance(layer, dict):
            continue
        for key, value in layer.items():
            if value is None or value == "":
                continue
            merged[str(key)] = value
    return merged


def param_inherited_from_slide(
    key: str,
    *,
    slide_filters: dict[str, Any] | None,
    block_params: dict[str, Any] | None,
) -> bool:
    slide = slide_filters if isinstance(slide_filters, dict) else {}
    block = block_params if isinstance(block_params, dict) else {}
    return key in slide and key not in block
