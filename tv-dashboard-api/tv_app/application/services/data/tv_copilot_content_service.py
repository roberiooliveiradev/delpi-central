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
    def setting_str(cls, key: str, default: str = "") -> str:
        settings = _load().get("settings") or {}
        value = settings.get(key, default)
        if value is None:
            return default
        return str(value)

    @classmethod
    def catalog_version(cls) -> str:
        return str(_load().get("catalogVersion") or "").strip()

    @classmethod
    def mutation_action_terms(cls) -> list[str]:
        raw = _load().get("mutationActionTerms")
        if not isinstance(raw, list):
            return []
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    @classmethod
    def create_action_terms(cls) -> list[str]:
        raw = _load().get("createActionTerms")
        if not isinstance(raw, list):
            return []
        return [str(item).strip().lower() for item in raw if str(item).strip()]

    @classmethod
    def action_terms_for_set(cls, term_set: str) -> list[str]:
        key = str(term_set or "").strip().lower()
        if key == "create":
            return cls.create_action_terms()
        if key == "mutation":
            return cls.mutation_action_terms()
        if key == "any":
            seen: set[str] = set()
            out: list[str] = []
            for term in [*cls.mutation_action_terms(), *cls.create_action_terms()]:
                if term in seen:
                    continue
                seen.add(term)
                out.append(term)
            return out
        return []

    @classmethod
    def placeholder_clarifications(cls) -> dict[str, str]:
        raw = _load().get("placeholderClarifications")
        if not isinstance(raw, dict):
            return {}
        return {
            str(key).strip(): str(value).strip()
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def op_field_clarifications(cls) -> dict[str, str]:
        raw = _load().get("opFieldClarifications")
        if not isinstance(raw, dict):
            return {}
        return {
            str(key).strip(): str(value).strip()
            for key, value in raw.items()
            if str(key).strip() and str(value).strip()
        }

    @classmethod
    def color_vocabulary(cls) -> dict[str, str]:
        raw = _load().get("colorVocabulary")
        if not isinstance(raw, dict):
            return {}
        out: dict[str, str] = {}
        for key, value in raw.items():
            name = str(key or "").strip().lower()
            hex_value = str(value or "").strip()
            if name and hex_value:
                out[name] = hex_value
        return out

    @classmethod
    def nl_route_hints(cls) -> dict[str, str]:
        raw = _load().get("nlRouteHints")
        if not isinstance(raw, dict):
            return {}
        out: dict[str, str] = {}
        for key, value in raw.items():
            alias = str(key or "").strip().lower()
            operation_id = str(value or "").strip()
            if alias and operation_id:
                out[alias] = operation_id
        return out

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
        fallback: dict[str, Any] | None = None
        for item in cls.capabilities():
            if str(item.get("op") or "").strip() != op_key:
                continue
            if bool(item.get("isComposite")):
                fallback = fallback or item
                continue
            return item
        return fallback

    @classmethod
    def allowed_ops(cls) -> frozenset[str]:
        caps = cls.capabilities()
        if caps:
            from_caps = {
                str(item.get("op") or "").strip()
                for item in caps
                if str(item.get("op") or "").strip() and not bool(item.get("isComposite"))
            }
            for item in caps:
                templates = item.get("payloadTemplates")
                if not isinstance(templates, list):
                    continue
                for template in templates:
                    if not isinstance(template, dict):
                        continue
                    op_name = str(template.get("op") or "").strip()
                    if op_name:
                        from_caps.add(op_name)
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
