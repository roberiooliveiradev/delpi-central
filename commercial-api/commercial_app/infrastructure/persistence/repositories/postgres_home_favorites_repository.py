from __future__ import annotations

import json
from typing import Any

from commercial_app.infrastructure.persistence.plugins.plugin_base_repository import (
    PluginBaseRepository,
)

MAX_HOME_FAVORITES = 20

ALLOWED_VIEW_IDS = frozenset(
    {
        "overview",
        "my_tasks",
        "open_orders",
        "customers",
        "proposals",
        "analytics_otd",
        "analytics_opportunities",
        "administration",
        "administration_portfolios",
        "administration_members",
    }
)


def normalize_favorite_items(raw: Any) -> list[dict[str, str]]:
    if not isinstance(raw, list):
        raise ValueError("items must be a list")
    if len(raw) > MAX_HOME_FAVORITES:
        raise ValueError(f"items exceeds max of {MAX_HOME_FAVORITES}")
    cleaned: list[dict[str, str]] = []
    seen: set[str] = set()
    for entry in raw:
        if not isinstance(entry, dict):
            raise ValueError("each item must be an object")
        view_id = str(entry.get("viewId") or "").strip()
        if not view_id or view_id not in ALLOWED_VIEW_IDS:
            raise ValueError(f"invalid viewId: {view_id}")
        search_raw = entry.get("search")
        search = None
        if search_raw is not None and str(search_raw).strip():
            search = str(search_raw).strip()
            if not search.startswith("?"):
                search = f"?{search}"
        key = f"{view_id}::{search or ''}"
        if key in seen:
            continue
        seen.add(key)
        item: dict[str, str] = {"viewId": view_id}
        if search:
            item["search"] = search
        cleaned.append(item)
    return cleaned


class PostgresHomeFavoritesRepository(PluginBaseRepository):
    def get_items(self, *, user_id: str) -> list[dict[str, str]]:
        row = self.fetch_one(
            """
            SELECT items
              FROM commercial.home_favorites
             WHERE user_id = %s
            """,
            (user_id,),
        )
        if not row:
            return []
        items = row.get("items") if isinstance(row, dict) else row[0]
        if isinstance(items, str):
            items = json.loads(items)
        try:
            return normalize_favorite_items(items or [])
        except ValueError:
            return []

    def put_items(self, *, user_id: str, items: list[dict[str, str]]) -> list[dict[str, str]]:
        cleaned = normalize_favorite_items(items)
        self.execute(
            """
            INSERT INTO commercial.home_favorites (user_id, items, updated_at)
            VALUES (%s, %s::jsonb, NOW())
            ON CONFLICT (user_id) DO UPDATE
               SET items = EXCLUDED.items,
                   updated_at = NOW()
            """,
            (user_id, json.dumps(cleaned)),
        )
        return cleaned
