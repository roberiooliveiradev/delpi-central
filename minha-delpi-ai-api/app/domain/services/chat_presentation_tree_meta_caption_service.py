"""Legendas humanizadas de meta em nós de árvore — chat base."""

from __future__ import annotations

from typing import Any

from app.domain.services.chat_presentation_vocabulary_service import (
    ChatPresentationVocabularyService,
)
from app.domain.services.external_actions.external_action_column_label_service import (
    ExternalActionColumnLabelService,
)


class ChatPresentationTreeMetaCaptionService:
    """Preenche ``metaCaption`` a partir de ``meta`` + ``column_labels.json``."""

    _LABELS = ExternalActionColumnLabelService()

    @classmethod
    def enrich(cls, presentation: dict[str, Any] | None, *, path: str = "") -> None:
        if not isinstance(presentation, dict) or presentation.get("type") != "tree":
            return

        root = presentation.get("root")

        if isinstance(root, dict):
            cls._enrich_node(root, path=path)

    @classmethod
    def _enrich_node(cls, node: dict[str, Any], *, path: str) -> None:
        meta = node.get("meta")

        if isinstance(meta, dict):
            cls._sync_quantity_alias(meta)
            cls._ensure_unit(meta)

            if not str(node.get("metaCaption") or "").strip():
                caption = cls._build_caption(meta)

                if caption:
                    node["metaCaption"] = caption

        for child in node.get("children") or []:
            if isinstance(child, dict):
                cls._enrich_node(child, path=path)

    @classmethod
    def _sync_quantity_alias(cls, meta: dict[str, Any]) -> None:
        quantity_field = cls._meta_caption_text("quantityField", default="quantity")

        if quantity_field in meta:
            return

        available_field = cls._meta_caption_text(
            "availableQuantityField",
            default="available_quantity",
        )

        if meta.get(available_field) is not None:
            meta[quantity_field] = float(meta[available_field])

    @classmethod
    def _ensure_unit(cls, meta: dict[str, Any]) -> None:
        unit_field = cls._meta_caption_text("unitField", default="unit")

        if unit_field not in meta or not str(meta.get(unit_field) or "").strip():
            meta[unit_field] = cls._meta_caption_text("defaultUnit", default="un.")

    @classmethod
    def _build_caption(cls, meta: dict[str, Any]) -> str:
        quantity_field = cls._meta_caption_text("quantityField", default="quantity")
        unit_field = cls._meta_caption_text("unitField", default="unit")
        field_order = cls._meta_caption_field_order()
        skip_fields = {
            quantity_field,
            unit_field,
            *cls._meta_caption_terms("skipFields"),
        }

        parts: list[str] = []

        for field in field_order:
            if field in skip_fields:
                continue

            value = meta.get(field)

            if value is None or not cls._is_numeric(value):
                continue

            label = cls._LABELS.label_for(field)
            parts.append(f"{label}: {cls._LABELS.format_num(value)}")

        if parts:
            unit = str(meta.get(unit_field) or "").strip()
            joined = " · ".join(parts)

            return f"{joined}{f' {unit}' if unit else ''}".strip()

        quantity = meta.get(quantity_field)

        if quantity is not None and cls._is_numeric(quantity):
            unit = str(meta.get(unit_field) or "").strip()
            formatted = cls._LABELS.format_num(quantity)

            return f"{formatted}{f' {unit}' if unit else ''}".strip()

        return ""

    @classmethod
    def _meta_caption_field_order(cls) -> tuple[str, ...]:
        ordered = cls._meta_caption_terms("fieldOrder")

        if ordered:
            return ordered

        return (
            "available_quantity",
            "current_quantity",
            "committed_quantity",
        )

    @classmethod
    def _meta_caption_text(cls, key: str, *, default: str = "") -> str:
        return ChatPresentationVocabularyService.text(
            "hierarchyTree",
            "metaCaption",
            key,
            default=default,
        )

    @classmethod
    def _meta_caption_terms(cls, key: str) -> tuple[str, ...]:
        return ChatPresentationVocabularyService.terms(
            "hierarchyTree",
            "metaCaption",
            key,
        )

    @staticmethod
    def _is_numeric(value: Any) -> bool:
        return isinstance(value, (int, float)) and not isinstance(value, bool)
