"""Árvore hierárquica a partir de itens planos agrupados — chat base."""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable


class ChatPresentationHierarchyTreeService:
    """Agrupa linhas tabulares em árvore (filial → armazém, categoria → item, etc.)."""

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
            "title": str(title or "").strip() or "Hierarquia",
            "root": cls._serialize_node(
                node_id=root_id or "root",
                label=root_label or root_id or "Raiz",
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
            "title": str(title or "").strip() or "Hierarquia",
            "root": cls._serialize_node(
                node_id=root_id or "root",
                label=root_label or root_id or "Raiz",
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
                        label=str(item.get("label") or item.get("code") or "—"),
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
            "label": str(label or "—"),
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
