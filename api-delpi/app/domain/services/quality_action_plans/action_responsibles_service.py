"""Normalização de múltiplos responsáveis por ação PAC."""

from __future__ import annotations

import re
from typing import Any

_LEGACY_NAME_SPLIT = re.compile(r"\s*/\s*")


def split_legacy_responsible_names(name: str | None) -> list[str]:
    raw = (name or "").strip()
    if not raw:
        return []
    if " / " in raw or "/" in raw:
        parts = [_part.strip() for _part in _LEGACY_NAME_SPLIT.split(raw)]
        return [part for part in parts if part]
    return [raw]


def normalize_responsible_entry(entry: Any) -> dict[str, Any] | None:
    if not isinstance(entry, dict):
        return None
    display_name = str(entry.get("display_name") or entry.get("name") or "").strip()
    if not display_name:
        return None
    user_id_raw = entry.get("user_id")
    user_id = str(user_id_raw).strip() if user_id_raw not in (None, "") else None
    return {
        "user_id": user_id or None,
        "display_name": display_name[:200],
    }


def normalize_responsibles_payload(
    responsibles: list[Any] | None,
    *,
    legacy_user_id: str | None = None,
    legacy_name: str | None = None,
) -> list[dict[str, Any]]:
    if responsibles is not None:
        normalized: list[dict[str, Any]] = []
        seen_users: set[str] = set()
        seen_names: set[str] = set()
        for entry in responsibles:
            item = normalize_responsible_entry(entry)
            if not item:
                continue
            user_key = item.get("user_id")
            name_key = str(item["display_name"]).casefold()
            if user_key:
                if user_key in seen_users:
                    continue
                seen_users.add(user_key)
            elif name_key in seen_names:
                continue
            else:
                seen_names.add(name_key)
            normalized.append(item)
        return normalized

    legacy_user = str(legacy_user_id).strip() if legacy_user_id else None
    legacy_names = split_legacy_responsible_names(legacy_name)
    if not legacy_names and not legacy_user:
        return []
    if not legacy_names:
        return [{"user_id": legacy_user, "display_name": "Responsável"}]
    result: list[dict[str, Any]] = []
    for index, name in enumerate(legacy_names):
        result.append(
            {
                "user_id": legacy_user if index == 0 else None,
                "display_name": name,
            }
        )
    return result


def build_legacy_action_responsible_fields(
    responsibles: list[dict[str, Any]],
) -> tuple[str | None, str | None]:
    if not responsibles:
        return None, None
    display_name = format_responsible_display_name(responsibles)
    first_user = next(
        (str(item["user_id"]).strip() for item in responsibles if item.get("user_id")),
        None,
    )
    return first_user or None, display_name or None


def format_responsible_display_name(responsibles: list[dict[str, Any]]) -> str:
    names: list[str] = []
    seen: set[str] = set()
    for item in responsibles:
        name = str(item.get("display_name") or "").strip()
        if not name:
            continue
        key = name.casefold()
        if key in seen:
            continue
        seen.add(key)
        names.append(name)
    return " / ".join(names)


def responsibles_from_legacy_action(action: dict[str, Any]) -> list[dict[str, Any]]:
    rows = action.get("responsibles")
    if isinstance(rows, list) and rows:
        return normalize_responsibles_payload(rows)
    return normalize_responsibles_payload(
        None,
        legacy_user_id=action.get("responsible_user_id"),
        legacy_name=action.get("responsible_name"),
    )
