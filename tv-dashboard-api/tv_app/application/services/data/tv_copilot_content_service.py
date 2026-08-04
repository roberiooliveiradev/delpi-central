"""Conteúdo PT do copiloto TV (patches tipados)."""

from __future__ import annotations

import json
from functools import lru_cache
from typing import Any

from pathlib import Path

CONTENT_PATH = Path(__file__).resolve().parents[3] / "content" / "tv_copilot_content.json"


@lru_cache(maxsize=1)
def _load() -> dict[str, Any]:
    return json.loads(CONTENT_PATH.read_text(encoding="utf-8"))


def clear_tv_copilot_content_cache() -> None:
    """Invalida o cache do JSON (testes / hot-reload)."""
    _load.cache_clear()


class TvCopilotContentService:
    @classmethod
    def message(cls, key: str, default: str = "", **format_kwargs: Any) -> str:
        messages = _load().get("messages") or {}
        text = str(messages.get(key) or default or key)
        if format_kwargs:
            try:
                return text.format_map(format_kwargs)
            except (KeyError, ValueError):
                return text
        return text

    @classmethod
    def setting_int(cls, key: str, default: int) -> int:
        settings = _load().get("settings") or {}
        try:
            return int(settings.get(key, default))
        except (TypeError, ValueError):
            return default

    @classmethod
    def catalog_version(cls) -> str:
        return str(_load().get("catalogVersion") or "").strip()

    @classmethod
    def capabilities(cls) -> list[dict[str, Any]]:
        raw = _load().get("capabilities")
        if not isinstance(raw, list):
            return []
        return [item for item in raw if isinstance(item, dict)]

    @classmethod
    def side_effect_hint_catalog(cls) -> list[str]:
        raw = _load().get("sideEffectHintCatalog")
        if not isinstance(raw, list):
            return []
        return [str(item).strip() for item in raw if str(item).strip()]

    @classmethod
    def capability_by_op(cls, op: str) -> dict[str, Any] | None:
        op_key = str(op or "").strip()
        if not op_key:
            return None
        for item in cls.capabilities():
            if str(item.get("op") or "").strip() == op_key:
                return item
        return None

    @classmethod
    def allowed_ops(cls) -> frozenset[str]:
        caps = cls.capabilities()
        if caps:
            from_caps = {
                str(item.get("op") or "").strip()
                for item in caps
                if str(item.get("op") or "").strip()
            }
            if from_caps:
                return frozenset(from_caps)
        raw = _load().get("allowedOps") or []
        return frozenset(str(item).strip() for item in raw if str(item).strip())

    @classmethod
    def capability_catalog_document(cls) -> dict[str, Any]:
        return {
            "catalogVersion": cls.catalog_version(),
            "capabilities": cls.capabilities(),
            "allowedOps": sorted(cls.allowed_ops()),
            "sideEffectHintCatalog": cls.side_effect_hint_catalog(),
        }

    @classmethod
    def side_effect_hints_for_op(cls, op: str) -> list[str]:
        cap = cls.capability_by_op(op)
        if not cap:
            return list(_FALLBACK_HINTS.get(op, ()))
        raw = cap.get("sideEffectHints")
        if isinstance(raw, list) and raw:
            return [str(item).strip() for item in raw if str(item).strip()]
        return list(_FALLBACK_HINTS.get(op, ()))


# Mapa de fallback se capability não declarar hints.
_FALLBACK_HINTS: dict[str, tuple[str, ...]] = {
    "upsert_data_source": ("replaceNativeConfig",),
    "set_data_transform": ("replaceNativeConfig",),
    "upsert_block": ("replaceNativeConfig",),
    "delete_block": ("replaceNativeConfig", "removeBlockIds"),
    "bind_visual": ("replaceNativeConfig",),
    "patch_native_config": ("replaceNativeConfig",),
    "add_slide_from_preset": ("refreshFilmstrip",),
    "add_blank_slide": ("refreshFilmstrip",),
    "update_slide": ("refreshFilmstrip",),
    "reorder_slides": ("refreshFilmstrip",),
    "delete_slide": ("refreshFilmstrip",),
    "upsert_section": ("refreshFilmstrip",),
    "delete_section": ("refreshFilmstrip",),
    "move_slide_to_section": ("refreshFilmstrip",),
    "create_playlist": ("refreshFilmstrip",),
}
