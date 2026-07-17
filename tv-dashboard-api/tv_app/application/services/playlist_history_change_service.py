from __future__ import annotations

from collections.abc import Mapping
from typing import Any


def _unavailable_change() -> dict[str, Any]:
    return {
        "available": False,
        "comparedToRevision": None,
        "playlistFields": [],
        "slides": {
            "added": [],
            "removed": [],
            "updated": [],
            "reordered": False,
        },
        "totals": {"added": 0, "removed": 0, "updated": 0},
    }


def _is_timestamp_field(field: str) -> bool:
    lowered = field.lower()
    return field.endswith("At") or lowered.endswith("_at") or "timestamp" in lowered


def _comparable(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _comparable(item)
            for key, item in value.items()
            if str(key) != "playlistId" and not _is_timestamp_field(str(key))
        }
    if isinstance(value, list):
        return [_comparable(item) for item in value]
    return value


def _snapshot_parts(
    snapshot: Any,
) -> tuple[dict[str, Any], list[dict[str, Any]], dict[str, dict[str, Any]]] | None:
    if not isinstance(snapshot, Mapping):
        return None
    playlist = snapshot.get("playlist")
    slides = snapshot.get("slides")
    if not isinstance(playlist, Mapping) or not isinstance(slides, list):
        return None

    normalized_slides: list[dict[str, Any]] = []
    slides_by_id: dict[str, dict[str, Any]] = {}
    for raw_slide in slides:
        if not isinstance(raw_slide, Mapping):
            return None
        slide = dict(raw_slide)
        slide_id = str(slide.get("id") or "").strip()
        if not slide_id or slide_id in slides_by_id:
            return None
        normalized_slides.append(slide)
        slides_by_id[slide_id] = slide
    return dict(playlist), normalized_slides, slides_by_id


class PlaylistHistoryChangeService:
    @staticmethod
    def unavailable() -> dict[str, Any]:
        return _unavailable_change()

    @staticmethod
    def compare(
        previous_snapshot: Any,
        next_snapshot: Any,
        *,
        compared_to_revision: int,
    ) -> dict[str, Any]:
        previous = _snapshot_parts(previous_snapshot)
        next_state = _snapshot_parts(next_snapshot)
        if previous is None or next_state is None:
            return _unavailable_change()

        previous_playlist, previous_slides, previous_by_id = previous
        next_playlist, next_slides, next_by_id = next_state

        playlist_fields = sorted(
            field
            for field in set(previous_playlist) | set(next_playlist)
            if field != "playlistId"
            and not _is_timestamp_field(field)
            and _comparable(previous_playlist.get(field))
            != _comparable(next_playlist.get(field))
        )

        previous_ids = [str(slide["id"]) for slide in previous_slides]
        next_ids = [str(slide["id"]) for slide in next_slides]
        previous_id_set = set(previous_ids)
        next_id_set = set(next_ids)

        added = [
            {"id": slide_id, "title": next_by_id[slide_id].get("title")}
            for slide_id in next_ids
            if slide_id not in previous_id_set
        ]
        removed = [
            {"id": slide_id, "title": previous_by_id[slide_id].get("title")}
            for slide_id in previous_ids
            if slide_id not in next_id_set
        ]

        updated: list[dict[str, Any]] = []
        ignored_slide_fields = {"id", "playlistId", "sortOrder"}
        for slide_id in next_ids:
            if slide_id not in previous_by_id:
                continue
            before = previous_by_id[slide_id]
            after = next_by_id[slide_id]
            fields = sorted(
                field
                for field in set(before) | set(after)
                if field not in ignored_slide_fields
                and not _is_timestamp_field(field)
                and _comparable(before.get(field)) != _comparable(after.get(field))
            )
            if fields:
                updated.append(
                    {"id": slide_id, "title": after.get("title"), "fields": fields}
                )

        common_ids = previous_id_set & next_id_set
        previous_common_order = [
            slide_id for slide_id in previous_ids if slide_id in common_ids
        ]
        next_common_order = [slide_id for slide_id in next_ids if slide_id in common_ids]
        reordered = previous_common_order != next_common_order

        return {
            "available": True,
            "comparedToRevision": int(compared_to_revision),
            "playlistFields": playlist_fields,
            "slides": {
                "added": added,
                "removed": removed,
                "updated": updated,
                "reordered": reordered,
            },
            "totals": {
                "added": len(added),
                "removed": len(removed),
                "updated": len(updated),
            },
        }
