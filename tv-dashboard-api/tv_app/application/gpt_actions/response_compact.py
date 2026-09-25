"""Compact projections for GPT Actions READ responses (≤ ~100 KiB budget)."""

from __future__ import annotations

import json
from typing import Any, Mapping

# OpenAI Custom GPT Actions tool response ceiling (ResponseTooLargeError).
GPT_ACTIONS_RESPONSE_MAX_BYTES = 100 * 1024

_MEDIA_ASSETS_CAP = 40
_CONTENT_PREVIEW_MAX_CHARS = 80
_BLOCK_INDEX_DEFAULT_LIMIT = 200
_BLOCK_INDEX_MAX_LIMIT = 500


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


def exceeds_actions_budget(payload: Any) -> bool:
    """True when any Actions serialization size would hit OpenAI ResponseTooLargeError."""
    return any(
        size > GPT_ACTIONS_RESPONSE_MAX_BYTES
        for size in actions_response_sizes(payload).values()
    )


_DROP_KEYS = frozenset(
    {
        "nativeConfig",
        "nativeConfigsBySlide",
        "persistedNative",
        "httpCommands",
        "resolved",
        "resolvedBySourceId",
        "resolvedByBlockId",
    }
)


def strip_heavy_mutation_blobs(value: Any, *, depth: int = 0) -> Any:
    """Remove nativeConfig/resolved blobs from GPT Actions public payloads/errors."""
    if depth > 12:
        return None
    if isinstance(value, dict):
        out: dict[str, Any] = {}
        for key, item in value.items():
            if str(key) in _DROP_KEYS:
                continue
            out[str(key)] = strip_heavy_mutation_blobs(item, depth=depth + 1)
        return out
    if isinstance(value, list):
        # Cap pathological lists in error details.
        capped = value[:80] if depth > 2 and len(value) > 80 else value
        return [strip_heavy_mutation_blobs(item, depth=depth + 1) for item in capped]
    return value


def project_mutation_actions_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
    """Public PREPARE/COMMIT projection that stays under Actions response budget."""
    raw = dict(payload) if isinstance(payload, dict) else {}
    out = strip_heavy_mutation_blobs(raw)
    if not isinstance(out, dict):
        out = {}

    # Prefer compact visual verification (issues only; no native).
    visual = out.get("visualVerification")
    if isinstance(visual, dict):
        out["visualVerification"] = {
            "persisted": bool(visual.get("persisted")),
            "rendered": bool(visual.get("rendered")),
            "layoutGatePassed": bool(visual.get("layoutGatePassed")),
            "issuesFixedCount": len(visual.get("issuesFixed") or []),
            "issuesIntroducedCount": len(visual.get("issuesIntroduced") or []),
            "remainingIssuesCount": len(visual.get("remainingIssues") or []),
            "remainingIssues": (visual.get("remainingIssues") or [])[:12],
        }

    candidate = out.get("candidatePreview")
    if isinstance(candidate, dict):
        out["candidatePreview"] = {
            "previewUrl": candidate.get("previewUrl"),
            "persisted": bool(candidate.get("persisted")),
            "remainingIssuesCount": len(candidate.get("remainingIssues") or []),
            "remainingIssues": (candidate.get("remainingIssues") or [])[:12],
        }

    # Drop nested verification that may still carry large checks.
    verification = out.get("verification")
    if isinstance(verification, dict):
        out["verification"] = {
            "reason": verification.get("reason"),
            "checks": [
                {
                    "op": item.get("op"),
                    "ok": item.get("ok"),
                    "reason": item.get("reason"),
                    "slideId": item.get("slideId"),
                }
                for item in (verification.get("checks") or [])
                if isinstance(item, dict)
            ][:40],
            "diff": (verification.get("diff") or [])[:20]
            if isinstance(verification.get("diff"), list)
            else None,
        }

    if exceeds_actions_budget(out):
        out.pop("candidatePreview", None)
        out.pop("fingerprint", None)
        out.pop("compileDigest", None)
        out.pop("aliasMap", None)
        out["responseCompacted"] = True
        out["note"] = (
            (str(out.get("note") or "") + " ").strip()
            + "Response compacted for Custom GPT Actions budget; "
            "proposal_handle/ops/persisted remain authoritative."
        ).strip()

    if exceeds_actions_budget(out):
        # Last resort: keep only commit/prepare essentials.
        essentials = {
            "target": out.get("target"),
            "ops": out.get("ops"),
            "operationNames": out.get("operationNames"),
            "proposal_handle": out.get("proposal_handle"),
            "catalogVersion": out.get("catalogVersion"),
            "baseRevision": out.get("baseRevision"),
            "risk": out.get("risk"),
            "confirmationPolicy": out.get("confirmationPolicy"),
            "confirmation_requirement": out.get("confirmation_requirement"),
            "canCommit": out.get("canCommit"),
            "persisted": out.get("persisted"),
            "verified": out.get("verified"),
            "status": out.get("status"),
            "revisionBefore": out.get("revisionBefore"),
            "revisionAfter": out.get("revisionAfter"),
            "commit_now_applied": out.get("commit_now_applied"),
            "message": out.get("message"),
            "diff": out.get("diff"),
            "outcome": out.get("outcome"),
            "responseCompacted": True,
            "note": "Minimal PREPARE/COMMIT projection (Actions response budget).",
        }
        return {k: v for k, v in essentials.items() if v is not None}

    return out


def project_editor_focus_context(
    *,
    playlist: Mapping[str, Any] | None,
    slides_index: list[dict[str, Any]],
    detail_slide: Mapping[str, Any] | None,
    data_sources: list[dict[str, Any]],
    selected_data_source_id: str | None,
    sections: Any,
    access_role: Any,
    revision: Any,
    editor_focus: Mapping[str, Any] | None = None,
    scope_downgraded: bool = False,
    slide_preview: Mapping[str, Any] | None = None,
    block_index: Mapping[str, Any] | None = None,
    object_matches: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    """Compact playlist context without focusedSlide.nativeConfig (rename-safe READ)."""
    focused_meta = None
    if isinstance(detail_slide, dict):
        focused_meta = {
            "id": detail_slide.get("id"),
            "title": detail_slide.get("title"),
            "sortOrder": detail_slide.get("sortOrder"),
            "durationSec": detail_slide.get("durationSec"),
            "isActive": detail_slide.get("isActive"),
            "slideType": detail_slide.get("slideType"),
            "sectionId": detail_slide.get("sectionId"),
        }
    selected_source = next(
        (
            row
            for row in data_sources
            if str(row.get("id") or "") == str(selected_data_source_id or "")
        ),
        None,
    )
    note = (
        "scope=editorFocus omits focusedSlide.nativeConfig and heavy digests. "
        "dataSources[] = data_source addressability (id/label/operationId/params). "
        "blockIndex = persisted visual/object addressability (id/type/frame/preview). "
        "editorFocus.selectedIds are hints, not required to resolve blockIds. "
        "Never invent UUID. Use scope=full only when nativeConfig is required."
    )
    if scope_downgraded:
        note = (
            "scope auto-downgraded to editorFocus: full nativeConfig exceeded the "
            "Custom GPT Actions response budget (ResponseTooLargeError). "
            "blockIndex + dataSources[] remain authoritative for existing-object "
            "resolution after downgrade. "
            + note
        )
    out: dict[str, Any] = {
        "scope": "editorFocus",
        "playlist": project_playlist_summary(playlist if isinstance(playlist, dict) else {}),
        "slides": slides_index,
        "focusedSlide": focused_meta,
        "focusedSlideId": str(detail_slide.get("id"))
        if isinstance(detail_slide, dict)
        else None,
        "dataSources": data_sources,
        "dataSource": selected_source,
        "sections": sections,
        "accessRole": access_role,
        "currentRevision": revision,
        "localDraftCoordination": "unavailable_external",
        "note": note,
    }
    if scope_downgraded:
        out["scopeDowngraded"] = True
        out["scopeDowngradeReason"] = "response_budget"
    if isinstance(block_index, dict) and block_index:
        out["blockIndex"] = dict(block_index)
    if isinstance(object_matches, list):
        out["objectMatches"] = object_matches
    if isinstance(slide_preview, dict) and slide_preview:
        out["slidePreview"] = dict(slide_preview)
    if isinstance(editor_focus, dict) and editor_focus:
        out = {"editorFocus": dict(editor_focus), **out}
    return fit_editor_focus_block_index(out)


def _block_frame(block: Mapping[str, Any]) -> dict[str, float] | None:
    raw = block.get("frame")
    if not isinstance(raw, dict):
        return None
    try:
        return {
            "x": round(float(raw.get("x", 0)), 2),
            "y": round(float(raw.get("y", 0)), 2),
            "w": round(float(raw.get("w", 0)), 2),
            "h": round(float(raw.get("h", 0)), 2),
        }
    except (TypeError, ValueError):
        return None


def _block_z_index(block: Mapping[str, Any]) -> int | None:
    style = block.get("style") if isinstance(block.get("style"), dict) else {}
    raw = style.get("zIndex", block.get("zIndex"))
    try:
        return int(raw) if raw is not None else None
    except (TypeError, ValueError):
        return None


def _truncate_preview(text: str, *, max_chars: int = _CONTENT_PREVIEW_MAX_CHARS) -> str:
    cleaned = " ".join(str(text or "").split())
    if len(cleaned) <= max_chars:
        return cleaned
    return cleaned[: max(1, max_chars - 1)].rstrip() + "…"


def content_preview_from_block(block: Mapping[str, Any]) -> str | None:
    """Short authored text for disambiguation — never resolved operational rows."""
    for key in ("content", "title", "label"):
        raw = block.get(key)
        if isinstance(raw, str) and raw.strip():
            return _truncate_preview(raw)
    binding = block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
    label = binding.get("label")
    if isinstance(label, str) and label.strip():
        return _truncate_preview(label)
    runs = block.get("contentRuns")
    if isinstance(runs, list):
        parts: list[str] = []
        for run in runs:
            if not isinstance(run, dict):
                continue
            if run.get("dataRef"):
                continue
            text = run.get("text")
            if isinstance(text, str) and text.strip():
                parts.append(text.strip())
            if sum(len(p) for p in parts) >= _CONTENT_PREVIEW_MAX_CHARS:
                break
        if parts:
            return _truncate_preview(" ".join(parts))
    return None


def binding_field_from_block(block: Mapping[str, Any]) -> str | None:
    """Cheap canonical binding field when present on authored projection/run."""
    projection = block.get("textProjection")
    if isinstance(projection, dict):
        field = str(projection.get("field") or "").strip()
        if field:
            return field
    runs = block.get("contentRuns")
    if isinstance(runs, list):
        for run in runs:
            if not isinstance(run, dict):
                continue
            ref = run.get("dataRef")
            if isinstance(ref, dict):
                field = str(ref.get("field") or "").strip()
                if field:
                    return field
    return None


def project_block_index_item(block: Mapping[str, Any]) -> dict[str, Any] | None:
    """One compact addressability row from a persisted block (no invented ids)."""
    if not isinstance(block, dict):
        return None
    block_id = str(block.get("id") or "").strip()
    btype = str(block.get("type") or "").strip()
    if not block_id or not btype:
        return None
    item: dict[str, Any] = {"id": block_id, "type": btype}
    frame = _block_frame(block)
    if frame:
        item["frame"] = frame
    z = _block_z_index(block)
    if z is not None:
        item["zIndex"] = z
    role = str(block.get("role") or "").strip()
    if role:
        item["role"] = role
    group_id = str(block.get("groupId") or "").strip()
    if group_id:
        item["groupId"] = group_id
    preview = content_preview_from_block(block)
    if preview:
        item["contentPreview"] = preview
    if btype == "data_source":
        binding = block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
        label = str(binding.get("label") or block.get("label") or "").strip()
        if label:
            item["label"] = _truncate_preview(label)
    elif isinstance(block.get("label"), str) and block.get("label").strip():
        item["label"] = _truncate_preview(str(block.get("label")))
    ds_id = str(block.get("dataSourceId") or "").strip()
    if ds_id:
        item["dataSourceId"] = ds_id
    binding_field = binding_field_from_block(block)
    if binding_field:
        item["bindingField"] = binding_field
        item["hasDataBinding"] = True
    elif ds_id or btype == "data_source":
        item["hasDataBinding"] = True
    return item


def _parse_block_cursor(raw: Any) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return 0
    return max(0, value)


def _parse_block_limit(raw: Any) -> int:
    try:
        value = int(raw)
    except (TypeError, ValueError):
        return _BLOCK_INDEX_DEFAULT_LIMIT
    if value <= 0:
        return _BLOCK_INDEX_DEFAULT_LIMIT
    return min(_BLOCK_INDEX_MAX_LIMIT, value)


def _normalize_object_types(raw: Any) -> set[str] | None:
    if raw is None:
        return None
    if isinstance(raw, str):
        parts = [p.strip() for p in raw.split(",") if p.strip()]
        return set(parts) if parts else None
    if isinstance(raw, (list, tuple, set)):
        parts = [str(p).strip() for p in raw if str(p).strip()]
        return set(parts) if parts else None
    return None


def _item_matches_object_query(item: Mapping[str, Any], query: str) -> bool:
    needle = query.strip().casefold()
    if not needle:
        return True
    haystacks = [
        str(item.get("contentPreview") or ""),
        str(item.get("label") or ""),
        str(item.get("groupId") or ""),
        str(item.get("role") or ""),
        str(item.get("bindingField") or ""),
        str(item.get("type") or ""),
        str(item.get("id") or ""),
    ]
    return any(needle in value.casefold() for value in haystacks if value)


def iter_block_index_items(
    native_config: Mapping[str, Any] | None,
    *,
    object_types: Any = None,
) -> list[dict[str, Any]]:
    """All compact items from persisted blocks (no pagination)."""
    cfg = native_config if isinstance(native_config, dict) else {}
    raw_blocks = cfg.get("blocks") if isinstance(cfg.get("blocks"), list) else []
    items: list[dict[str, Any]] = []
    type_filter = _normalize_object_types(object_types)
    for block in raw_blocks:
        row = project_block_index_item(block if isinstance(block, dict) else {})
        if row is None:
            continue
        if type_filter is not None and str(row.get("type") or "") not in type_filter:
            continue
        items.append(row)
    return items


def project_block_index(
    native_config: Mapping[str, Any] | None,
    *,
    slide_id: str | None,
    revision: Any,
    cursor: Any = 0,
    limit: Any = None,
    object_types: Any = None,
) -> dict[str, Any]:
    """Compact READ addressability for persisted blocks (budget-safe projection)."""
    items = iter_block_index_items(native_config, object_types=object_types)

    total = len(items)
    offset = _parse_block_cursor(cursor)
    page_limit = _parse_block_limit(limit if limit is not None else _BLOCK_INDEX_DEFAULT_LIMIT)
    page = items[offset : offset + page_limit]
    returned = len(page)
    truncated = offset + returned < total
    next_cursor = str(offset + returned) if truncated else None
    return {
        "slideId": slide_id,
        "revision": revision,
        "total": total,
        "returned": returned,
        "truncated": truncated,
        "nextCursor": next_cursor,
        "offset": offset,
        "items": page,
    }


def fit_editor_focus_block_index(payload: dict[str, Any]) -> dict[str, Any]:
    """Shrink blockIndex page until the editorFocus payload fits Actions budget."""
    if not exceeds_actions_budget(payload):
        return payload
    index = payload.get("blockIndex")
    if not isinstance(index, dict):
        return payload
    items = index.get("items")
    if not isinstance(items, list) or not items:
        return payload
    try:
        offset = max(0, int(index.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0
    try:
        total = max(len(items), int(index.get("total") or len(items)))
    except (TypeError, ValueError):
        total = len(items)

    low, high = 1, len(items)
    best: dict[str, Any] | None = None
    while low <= high:
        mid = (low + high) // 2
        page = items[:mid]
        candidate = dict(payload)
        next_index = dict(index)
        next_index["items"] = page
        next_index["returned"] = len(page)
        next_index["offset"] = offset
        end = offset + len(page)
        next_index["truncated"] = end < total
        next_index["nextCursor"] = str(end) if end < total else None
        candidate["blockIndex"] = next_index
        if not exceeds_actions_budget(candidate):
            best = candidate
            low = mid + 1
        else:
            high = mid - 1
    return best if isinstance(best, dict) else payload


def project_object_matches(
    items: list[dict[str, Any]],
    *,
    object_query: str | None,
    object_types: Any = None,
    limit: int = 40,
) -> list[dict[str, Any]] | None:
    """Optional filtered candidates from persisted projection items (no new IDs)."""
    query = str(object_query or "").strip()
    type_filter = _normalize_object_types(object_types)
    if not query and type_filter is None:
        return None
    matches: list[dict[str, Any]] = []
    for item in items:
        if not isinstance(item, dict):
            continue
        if type_filter is not None and str(item.get("type") or "") not in type_filter:
            continue
        if query and not _item_matches_object_query(item, query):
            continue
        matches.append(dict(item))
        if len(matches) >= max(1, limit):
            break
    return matches


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


def project_data_source_row(block: Mapping[str, Any]) -> dict[str, Any] | None:
    """Compact data_source digest for mutation planning (no resolved payload)."""
    if not isinstance(block, dict):
        return None
    if str(block.get("type") or "").strip() != "data_source":
        return None
    binding = block.get("dataBinding") if isinstance(block.get("dataBinding"), dict) else {}
    params = binding.get("params") if isinstance(binding.get("params"), dict) else {}
    transform = block.get("dataTransform") if isinstance(block.get("dataTransform"), dict) else None
    return {
        "id": block.get("id"),
        "label": binding.get("label") or block.get("label") or "",
        "operationId": binding.get("operationId") or "",
        "params": dict(params),
        "displayMode": binding.get("displayMode") or "auto",
        "hasTransform": bool(
            isinstance(transform, dict)
            and (
                (isinstance(transform.get("steps"), list) and transform.get("steps"))
                or transform.get("script")
            )
        ),
        "fieldLabels": block.get("fieldLabels")
        if isinstance(block.get("fieldLabels"), dict)
        else {},
    }


def project_data_sources_from_slide(slide: Mapping[str, Any] | None) -> list[dict[str, Any]]:
    if not isinstance(slide, dict):
        return []
    native = slide.get("nativeConfig") if isinstance(slide.get("nativeConfig"), dict) else {}
    blocks = native.get("blocks") if isinstance(native.get("blocks"), list) else []
    out: list[dict[str, Any]] = []
    for block in blocks:
        row = project_data_source_row(block)
        if row is not None:
            out.append(row)
    return out


def resolve_selected_data_source_id(
    *,
    editor_focus: Mapping[str, Any] | None,
    data_sources: list[Mapping[str, Any]],
) -> str | None:
    """Prefer explicit selectedDataSourceId; else first selectedIds that is a data_source."""
    if isinstance(editor_focus, dict):
        explicit = str(editor_focus.get("selectedDataSourceId") or "").strip()
        if explicit:
            return explicit
        source_ids = {
            str(item.get("id") or "").strip()
            for item in data_sources
            if str(item.get("id") or "").strip()
        }
        selected = editor_focus.get("selectedIds")
        if isinstance(selected, list):
            for item in selected:
                sid = str(item or "").strip()
                if sid and sid in source_ids:
                    return sid
    return None


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
