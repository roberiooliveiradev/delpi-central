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
        "dataSources[] lists id/label/operationId/params for the focused slide. "
        "dataSource is the selected source when editorFocus.selectedDataSourceId "
        "or selectedIds resolve to a data_source. Use scope=full for nativeConfig."
    )
    if scope_downgraded:
        note = (
            "scope auto-downgraded to editorFocus: full nativeConfig exceeded the "
            "Custom GPT Actions response budget (ResponseTooLargeError). "
            "dataSources[] / dataSource remain authoritative for label rename. "
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
    if isinstance(slide_preview, dict) and slide_preview:
        out["slidePreview"] = dict(slide_preview)
    if isinstance(editor_focus, dict) and editor_focus:
        out = {"editorFocus": dict(editor_focus), **out}
    return out


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
