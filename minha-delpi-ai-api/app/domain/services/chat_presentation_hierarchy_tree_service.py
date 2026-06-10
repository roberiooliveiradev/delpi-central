"""Árvore hierárquica a partir de itens planos agrupados — chat base."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class ChatPresentationHierarchyTreeService:
    """Agrupa linhas tabulares em árvore (filial → armazém, categoria → item, etc.)."""

    @classmethod
    def _hierarchy_title(cls, title: str) -> str:
        from app.domain.services.chat_presentation_vocabulary_service import (
            ChatPresentationVocabularyService,
        )

        return str(title or "").strip() or ChatPresentationVocabularyService.hierarchy_tree_text(
            "defaultHierarchyTitle",
            default="Hierarquia",
        )

    @classmethod
    def _structure_title(cls, title: str) -> str:
        from app.domain.services.chat_presentation_vocabulary_service import (
            ChatPresentationVocabularyService,
        )

        return str(title or "").strip() or ChatPresentationVocabularyService.hierarchy_tree_text(
            "defaultStructureTitle",
            default="Estrutura",
        )

    @classmethod
    def _root_label(cls, root_label: str, root_id: str) -> str:
        from app.domain.services.chat_presentation_vocabulary_service import (
            ChatPresentationVocabularyService,
        )

        return (
            str(root_label or "").strip()
            or str(root_id or "").strip()
            or ChatPresentationVocabularyService.hierarchy_tree_text("defaultRootLabel", default="Raiz")
        )

    @classmethod
    def _empty_label(cls) -> str:
        from app.domain.services.chat_presentation_vocabulary_service import (
            ChatPresentationVocabularyService,
        )

        return ChatPresentationVocabularyService.hierarchy_tree_text("emptyLabel", default="—")

    @classmethod
    def build_from_grouped_items(
        cls,
        *,
        title: str,
        root_id: str,
        root_label: str,
        root_subtitle: str = "",
        items: list[dict[str, Any]],
        group_keys: list[str],
        leaf_builder: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
    ) -> dict[str, Any] | None:
        if not items or not group_keys:
            return None

        tree_root = cls._build_group_level(
            items,
            group_keys=group_keys,
            depth=0,
            leaf_builder=leaf_builder,
        )

        if not tree_root:
            return None

        return {
            "type": "tree",
            "title": cls._hierarchy_title(title),
            "root": cls._serialize_node(
                node_id=root_id or "root",
                label=cls._root_label(root_label, root_id),
                subtitle=root_subtitle,
                children=[tree_root] if group_keys else None,
            ),
        }

    @classmethod
    def build_multi_level(
        cls,
        *,
        title: str,
        root_id: str,
        root_label: str,
        root_subtitle: str = "",
        items: list[dict[str, Any]],
        group_keys: list[str],
        leaf_builder: Callable[[dict[str, Any]], dict[str, Any] | None] | None = None,
    ) -> dict[str, Any] | None:
        if not items or not group_keys:
            return None

        children = cls._build_children(
            items,
            group_keys=group_keys,
            depth=0,
            leaf_builder=leaf_builder,
        )

        if not children:
            return None

        return {
            "type": "tree",
            "title": cls._hierarchy_title(title),
            "root": cls._serialize_node(
                node_id=root_id or "root",
                label=cls._root_label(root_label, root_id),
                subtitle=root_subtitle,
                children=children,
            ),
        }

    @classmethod
    def _build_group_level(
        cls,
        items: list[dict[str, Any]],
        *,
        group_keys: list[str],
        depth: int,
        leaf_builder: Callable[[dict[str, Any]], dict[str, Any] | None] | None,
    ) -> dict[str, Any] | None:
        children = cls._build_children(
            items,
            group_keys=group_keys,
            depth=depth,
            leaf_builder=leaf_builder,
        )

        if not children:
            return None

        return children[0] if len(children) == 1 and depth == 0 else None

    @classmethod
    def _build_children(
        cls,
        items: list[dict[str, Any]],
        *,
        group_keys: list[str],
        depth: int,
        leaf_builder: Callable[[dict[str, Any]], dict[str, Any] | None] | None,
    ) -> list[dict[str, Any]]:
        if depth >= len(group_keys):
            nodes: list[dict[str, Any]] = []

            for item in items:
                if not isinstance(item, dict):
                    continue

                if leaf_builder:
                    built = leaf_builder(item)

                    if built:
                        nodes.append(built)
                        continue

                nodes.append(
                    cls._serialize_node(
                        node_id=str(item.get("id") or item.get("code") or len(nodes)),
                        label=str(item.get("label") or item.get("code") or cls._empty_label()),
                        subtitle=str(item.get("description") or "").strip(),
                        meta=cls._numeric_meta(item),
                    )
                )

            return nodes

        key = group_keys[depth]
        buckets: dict[str, list[dict[str, Any]]] = defaultdict(list)

        for item in items:
            if not isinstance(item, dict):
                continue

            bucket_key = str(item.get(key) or "—").strip() or "—"
            buckets[bucket_key].append(item)

        nodes: list[dict[str, Any]] = []

        for bucket_key in sorted(buckets.keys()):
            bucket_items = buckets[bucket_key]
            child_nodes = cls._build_children(
                bucket_items,
                group_keys=group_keys,
                depth=depth + 1,
                leaf_builder=leaf_builder,
            )

            nodes.append(
                cls._serialize_node(
                    node_id=f"{key}:{bucket_key}",
                    label=bucket_key,
                    badge=str(key).upper(),
                    children=child_nodes or None,
                    meta=cls._aggregate_meta(bucket_items),
                )
            )

        return nodes

    @classmethod
    def _numeric_meta(cls, item: dict[str, Any]) -> dict[str, str | float | int]:
        meta: dict[str, str | float | int] = {}

        for field, value in item.items():
            if isinstance(value, (int, float)) and field not in {"id", "rank"}:
                meta[str(field)] = value

        return meta

    @classmethod
    def _aggregate_meta(cls, items: list[dict[str, Any]]) -> dict[str, float | int]:
        totals: dict[str, float] = {}

        for item in items:
            if not isinstance(item, dict):
                continue

            for field, value in item.items():
                if isinstance(value, (int, float)):
                    totals[str(field)] = totals.get(str(field), 0.0) + float(value)

        return {key: (int(value) if value == int(value) else value) for key, value in totals.items()}

    @classmethod
    def _serialize_node(
        cls,
        *,
        node_id: str,
        label: str,
        subtitle: str = "",
        badge: str = "",
        children: list[dict[str, Any]] | None = None,
        meta: dict[str, str | float | int] | None = None,
    ) -> dict[str, Any]:
        node: dict[str, Any] = {
            "id": str(node_id or "node"),
            "label": str(label or cls._empty_label()),
        }

        if subtitle:
            node["subtitle"] = subtitle

        if badge:
            node["badge"] = badge

        if meta:
            node["meta"] = meta

        if children:
            node["children"] = children

        return node

    @classmethod
    def build_flat_bom_tree(
        cls,
        *,
        title: str,
        root_id: str,
        root_label: str,
        root_subtitle: str = "",
        items: list[dict[str, Any]],
        meta_keys: tuple[str, ...] = (
            "accumulated_quantity",
            "quantity_per",
            "component_unit",
            "exclusive_raw_material_label",
            "total_valid_finished_products_using_mp",
        ),
    ) -> dict[str, Any] | None:
        normalized = cls._normalize_flat_bom_items(items, root_id=root_id)

        if not normalized:
            return None

        nodes_by_code: dict[str, dict[str, Any]] = {}

        for row in normalized:
            nodes_by_code[row["code"]] = cls._serialize_flat_bom_node(row, meta_keys=meta_keys)

        root_children: list[dict[str, Any]] = []

        for row in normalized:
            code = row["code"]
            parent_code = row["parent_code"]
            node = nodes_by_code[code]

            if parent_code and parent_code in nodes_by_code and parent_code != code:
                parent_node = nodes_by_code[parent_code]
                children = parent_node.setdefault("children", [])

                if node not in children:
                    children.append(node)

                continue

            if parent_code == root_id or row.get("level") == 1:
                if node not in root_children:
                    root_children.append(node)

        if not root_children:
            root_children = list(nodes_by_code.values())

        return {
            "type": "tree",
            "title": cls._structure_title(title),
            "root": cls._serialize_node(
                node_id=root_id or "root",
                label=cls._root_label(root_label, root_id),
                subtitle=root_subtitle,
                children=root_children or None,
            ),
        }

    @classmethod
    def _normalize_flat_bom_items(
        cls,
        items: list[dict[str, Any]],
        *,
        root_id: str,
    ) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            code = str(
                item.get("component_code")
                or item.get("product_code")
                or ""
            ).strip()

            if not code:
                continue

            parent_code = str(item.get("parent_code") or "").strip() or root_id
            description = str(
                item.get("component_description")
                or item.get("description")
                or ""
            ).strip()
            component_type = str(item.get("component_type") or "").strip()
            unit = str(item.get("component_unit") or item.get("unit") or "").strip()

            try:
                level = int(item.get("level") or 0)
            except (TypeError, ValueError):
                level = 0

            normalized.append(
                {
                    "code": code,
                    "parent_code": parent_code,
                    "description": description,
                    "component_type": component_type,
                    "unit": unit,
                    "level": level,
                    "raw": item,
                }
            )

        normalized.sort(key=lambda row: (row.get("level") or 0, row["code"]))

        return normalized

    @classmethod
    def _serialize_flat_bom_node(
        cls,
        row: dict[str, Any],
        *,
        meta_keys: tuple[str, ...],
    ) -> dict[str, Any]:
        item = row.get("raw") if isinstance(row.get("raw"), dict) else {}
        code = str(row.get("code") or cls._empty_label())
        component_type = str(row.get("component_type") or "").strip()
        label = f"{code} ({component_type})" if component_type else code
        meta: dict[str, str | float | int] = {}

        for key in meta_keys:
            value = item.get(key)

            if value in (None, ""):
                continue

            if isinstance(value, (int, float)):
                meta[str(key)] = value
            else:
                meta[str(key)] = str(value).strip()

        return cls._serialize_node(
            node_id=f"bom:{code}",
            label=label,
            subtitle=str(row.get("description") or "").strip(),
            badge=component_type,
            meta=meta or None,
        )
