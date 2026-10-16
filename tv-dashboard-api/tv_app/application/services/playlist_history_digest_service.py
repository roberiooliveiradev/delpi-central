"""P9 V1 — agent-safe projection over the canonical playlist history domain.

Owner of the model-facing digest only. Persistence, retention, diff and
AuthZ stay with PlaylistHistoryRepository / PlaylistHistoryChangeService /
PlaylistAccessService — this module never touches storage, never diffs,
never authorizes.

Projection rules (P9 V1, §44):
- no raw snapshot: nativeConfig, masterConfig, dataDefaults, externalUrl,
  externalSandbox and the `playlist` detail payload are never projected;
- actor identity minimized: actor name only — never email or user id;
- `reason` is mutation provenance, IS_NOT user motivation: only
  allowlisted technical codes pass through as `mutationProvenance`;
  free-form/unknown values (e.g. user-supplied restore text) are omitted;
- block-level diff claims are impossible here by construction: the digest
  carries slide-field granularity verbatim from the canonical diff and
  never descends into nativeConfig.blocks.
"""

from __future__ import annotations

from typing import Any

from tv_app.infrastructure.persistence.repositories.playlist_history_repository import (
    HISTORY_LIMIT_PER_PLAYLIST,
    PlaylistHistoryNotFoundError,
)

__all__ = [
    "PlaylistHistoryNotFoundError",
    "TECHNICAL_PROVENANCE_CODES",
    "history_detail_projection",
    "history_item_digest",
    "history_list_projection",
]

# Bounded technical provenance vocabulary observed in the write pipeline
# (PlaylistRepository._capture_before_mutation call sites). Anything else —
# including free-form user text from restore — is omitted.
TECHNICAL_PROVENANCE_CODES: frozenset[str] = frozenset(
    {
        "activated",
        "created",
        "deactivated",
        "deleted",
        "duplicated",
        "history_restored",
        "imported",
        "media_deleted",
        "media_optimized",
        "media_uploaded",
        "playlist_activated",
        "playlist_data_defaults",
        "playlist_deactivated",
        "playlist_deleted",
        "playlist_imported",
        "playlist_imported_activated",
        "playlist_imported_sections",
        "playlist_imported_slides",
        "playlist_updated",
        "presentation_blank_slide",
        "presentation_delete_section",
        "presentation_delete_slide",
        "presentation_move_slide_section",
        "presentation_mutation",
        "presentation_playlist_created",
        "presentation_playlist_seed",
        "presentation_reorder_slides",
        "presentation_slide_from_preset",
        "presentation_update_slide",
        "presentation_upsert_section",
        "section_created",
        "section_deleted",
        "section_main_ensured",
        "section_updated",
        "sections_reordered",
        "shared",
        "slide_created",
        "slide_deleted",
        "slide_duplicated",
        "slide_imported",
        "slide_updated",
        "slides_reordered",
        "token_regenerated",
        "updated",
        # observed in runtime rows (copilot-era write paths)
        "copilot_patch_applied",
        "copilot_slide_from_preset",
        "copilot_blank_slide",
    }
)


def _provenance(reason: Any) -> str | None:
    code = str(reason or "").strip()
    return code if code in TECHNICAL_PROVENANCE_CODES else None


def history_item_digest(item: dict[str, Any]) -> dict[str, Any]:
    """Project one repository summary row (+canonical change) to a digest."""
    preview = item.get("preview") if isinstance(item.get("preview"), dict) else {}
    change = item.get("change") if isinstance(item.get("change"), dict) else {}
    slides = change.get("slides") if isinstance(change.get("slides"), dict) else {}
    return {
        "snapshotId": item.get("snapshotId"),
        "revision": item.get("revision"),
        "createdAt": item.get("createdAt"),
        "actor": {"name": item.get("authorName")},
        "mutationProvenance": _provenance(item.get("reason")),
        "preview": {
            "playlistName": preview.get("playlistName"),
            "slideCount": preview.get("slideCount"),
            "slideTitles": list(preview.get("slideTitles") or [])[:3],
        },
        # Canonical diff verbatim — bounded field names only, never values.
        "change": {
            "available": bool(change.get("available")),
            "comparedToRevision": change.get("comparedToRevision"),
            "playlistFields": list(change.get("playlistFields") or []),
            "slides": {
                "added": [
                    {"id": s.get("id"), "title": s.get("title")}
                    for s in slides.get("added") or []
                    if isinstance(s, dict)
                ],
                "removed": [
                    {"id": s.get("id"), "title": s.get("title")}
                    for s in slides.get("removed") or []
                    if isinstance(s, dict)
                ],
                "updated": [
                    {
                        "id": s.get("id"),
                        "title": s.get("title"),
                        "fields": list(s.get("fields") or []),
                    }
                    for s in slides.get("updated") or []
                    if isinstance(s, dict)
                ],
                "reordered": bool(slides.get("reordered")),
            },
            "totals": dict(change.get("totals") or {}),
        },
    }


def history_list_projection(
    payload: dict[str, Any], *, playlist_id: str
) -> dict[str, Any]:
    """List mode envelope — bounded digest items + retention truth."""
    items = payload.get("items") if isinstance(payload.get("items"), list) else []
    return {
        "mode": "list",
        "playlistId": playlist_id,
        "currentRevision": payload.get("currentRevision"),
        "currentSnapshotId": payload.get("currentSnapshotId"),
        "retention": {
            "maxSnapshots": HISTORY_LIMIT_PER_PLAYLIST,
            "completeHistoryGuaranteed": False,
        },
        "page": payload.get("page"),
        "pageSize": payload.get("pageSize"),
        "total": payload.get("total"),
        "totalPages": payload.get("totalPages"),
        "items": [history_item_digest(item) for item in items],
    }


def history_detail_projection(payload: dict[str, Any]) -> dict[str, Any]:
    """Detail mode = the same bounded digest of one snapshot.

    The raw `playlist` snapshot in the repository detail payload is
    intentionally never projected — detail mode adds no raw state.
    """
    digest = history_item_digest(payload)
    digest["mode"] = "detail"
    return digest
