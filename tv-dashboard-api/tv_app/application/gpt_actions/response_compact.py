"""Compact projections for GPT Actions READ responses (≤ ~100 KiB budget)."""

from __future__ import annotations

import json
from typing import Any, Mapping

# OpenAI Custom GPT Actions tool response ceiling (ResponseTooLargeError).
GPT_ACTIONS_RESPONSE_MAX_BYTES = 100 * 1024

_MEDIA_ASSETS_CAP = 40


def utf8_size(payload: Any) -> int:
    return len(json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8"))


def ascii_utf8_size(payload: Any) -> int:
    """Byte size with ASCII escapes — closer to Custom GPT Actions serialization."""
    return len(json.dumps(payload, ensure_ascii=True, default=str).encode("utf-8"))


def actions_response_sizes(payload: Any) -> dict[str, int]:
    """Sizes that must all stay ≤ ``GPT_ACTIONS_RESPONSE_MAX_BYTES``."""
    return {
        "unicode": utf8_size(payload),
        "ascii": ascii_utf8_size(payload),
        "envelopeAscii": ascii_utf8_size({"success": True, "data": payload}),
    }


def _block_type_summary(native_config: Mapping[str, Any] | None) -> dict[str, Any]:
    cfg = native_config if isinstance(native_config, dict) else {}
    blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
    types: list[str] = []
    for block in blocks:
        if not isinstance(block, dict):
            continue
        btype = str(block.get("type") or "").strip()
        if btype and btype != "data_source":
            types.append(btype)
    return {
        "blockCount": len(types),
        "blockTypes": sorted(set(types))[:12],
    }


def strip_resolved_from_native(native_config: Any) -> Any:
    """Drop runtime resolved payloads from blocks (not needed for mutation planning)."""
    if not isinstance(native_config, dict):
        return native_config
    out = dict(native_config)
    blocks = out.get("blocks")
    if not isinstance(blocks, list):
        return out
    cleaned: list[Any] = []
    for block in blocks:
        if not isinstance(block, dict):
            cleaned.append(block)
            continue
        row = dict(block)
        row.pop("resolved", None)
        cleaned.append(row)
    out["blocks"] = cleaned
    return out


def project_playlist_list_item(item: Mapping[str, Any], *, access_role: str) -> dict[str, Any]:
    """Home-grade cover/native blobs stay out of GPT list (budget + clarity)."""
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "description": item.get("description"),
        "isActive": item.get("isActive"),
        "revision": item.get("revision"),
        "updatedAt": item.get("updatedAt"),
        "viewportProfile": item.get("viewportProfile"),
        "accessRole": access_role,
        "hasDataDefaults": bool(
            isinstance(item.get("dataDefaults"), dict) and item.get("dataDefaults")
        ),
    }


def project_slide_index_row(slide: Mapping[str, Any]) -> dict[str, Any]:
    native = slide.get("nativeConfig") if isinstance(slide.get("nativeConfig"), dict) else {}
    summary = _block_type_summary(native)
    return {
        "id": slide.get("id"),
        "title": slide.get("title"),
        "sortOrder": slide.get("sortOrder"),
        "durationSec": slide.get("durationSec"),
        "isActive": slide.get("isActive"),
        "slideType": slide.get("slideType"),
        "nativeScreenKey": slide.get("nativeScreenKey"),
        "sectionId": slide.get("sectionId"),
        **summary,
    }


def project_slide_detail(slide: Mapping[str, Any]) -> dict[str, Any]:
    row = {
        "id": slide.get("id"),
        "title": slide.get("title"),
        "sortOrder": slide.get("sortOrder"),
        "durationSec": slide.get("durationSec"),
        "isActive": slide.get("isActive"),
        "slideType": slide.get("slideType"),
        "nativeScreenKey": slide.get("nativeScreenKey"),
        "sectionId": slide.get("sectionId"),
        "transitionStyle": slide.get("transitionStyle"),
        "nativeConfig": strip_resolved_from_native(slide.get("nativeConfig")),
    }
    return row


def project_playlist_summary(playlist: Mapping[str, Any] | None) -> dict[str, Any]:
    if not isinstance(playlist, dict):
        return {}
    return {
        "id": playlist.get("id"),
        "name": playlist.get("name"),
        "description": playlist.get("description"),
        "isActive": playlist.get("isActive"),
        "revision": playlist.get("revision"),
        "updatedAt": playlist.get("updatedAt"),
        "viewportProfile": playlist.get("viewportProfile"),
        "transitionStyle": playlist.get("transitionStyle"),
        "defaultDurationSec": playlist.get("defaultDurationSec"),
        "dataDefaults": playlist.get("dataDefaults")
        if isinstance(playlist.get("dataDefaults"), dict)
        else {},
    }


def project_media_inventory(
    *,
    brand_logos: Mapping[str, Any],
    assets: list[dict[str, Any]],
) -> dict[str, Any]:
    capped = assets[:_MEDIA_ASSETS_CAP]
    return {
        "brandLogos": dict(brand_logos),
        "assets": capped,
        "assetsTotal": len(assets),
        "assetsTruncated": len(assets) > len(capped),
        "note": (
            "Brand logos are ASSET_ID_ONLY. assets[] lists playlist library media "
            f"(cap {_MEDIA_ASSETS_CAP}; see assetsTotal). "
            "Call ensure_brand_logo_on_slide to seed missing packaged Delpi logos."
        ),
    }


def pick_focus_slide_id(
    slides: list[dict[str, Any]],
    *,
    editor_focus: Mapping[str, Any] | None,
    preview_slide_id: str | None = None,
) -> str | None:
    explicit = (preview_slide_id or "").strip()
    if explicit:
        return explicit
    if isinstance(editor_focus, dict):
        sid = str(editor_focus.get("slideId") or "").strip()
        if sid:
            return sid
    if slides:
        return str(slides[0].get("id") or "").strip() or None
    return None
