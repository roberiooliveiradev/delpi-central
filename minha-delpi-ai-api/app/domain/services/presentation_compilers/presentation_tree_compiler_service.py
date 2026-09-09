"""Compila spec.tree.levelFields → treePresentation nodes (sem inventar hierarquia)."""

from __future__ import annotations

from typing import Any

from app.domain.entities.presentation_data_profile import PresentationDataProfile
from app.domain.entities.presentation_spec import PresentationSpec
from app.domain.services.presentation_compilers.presentation_chart_compiler_service import (
    PresentationChartCompilerService,
)


class PresentationTreeCompilerService:
    @classmethod
    def apply(
        cls,
        metadata: dict[str, Any],
        *,
        spec: PresentationSpec,
        profile: PresentationDataProfile,
        labels: dict[str, str],
    ) -> None:
        if spec.tree is None or not spec.tree.level_fields:
            return

        level_fields = list(spec.tree.level_fields)
        if not cls._has_hierarchical_dimensions(level_fields, profile):
            decision = metadata.setdefault("presentationDecision", {})
            if isinstance(decision, dict):
                decision["unmetIntent"] = "tree_not_materializable"
            return

        rows = cls._tabular_rows(metadata)
        if not rows:
            decision = metadata.setdefault("presentationDecision", {})
            if isinstance(decision, dict):
                decision["unmetIntent"] = "tree_not_materializable"
            return

        root_nodes = cls._build_nodes_from_rows(
            rows,
            level_fields=level_fields,
            label_field=spec.tree.label_field,
            badge_field=spec.tree.badge_field,
            labels=labels,
            max_depth=spec.tree.max_depth,
        )
        if not root_nodes:
            decision = metadata.setdefault("presentationDecision", {})
            if isinstance(decision, dict):
                decision["unmetIntent"] = "tree_not_materializable"
            return

        tree = metadata.get("treePresentation")
        if not isinstance(tree, dict) and isinstance(metadata.get("presentation"), dict):
            if metadata["presentation"].get("type") == "tree":
                tree = metadata["presentation"]

        title = (
            (isinstance(tree, dict) and str(tree.get("title") or "").strip())
            or "Estrutura"
        )
        payload: dict[str, Any] = {
            "type": "tree",
            "title": title,
            "root": root_nodes[0] if len(root_nodes) == 1 else {"id": "root", "label": title, "children": root_nodes},
        }
        if spec.tree.default_expanded_depth is not None:
            payload["defaultExpandedDepth"] = spec.tree.default_expanded_depth

        config = dict((tree or {}).get("config") or {})
        config["bindingProvenance"] = "COMPILED"
        config["levelFields"] = level_fields
        payload["config"] = config

        metadata["treePresentation"] = payload
        if metadata.get("presentation") is tree or (
            isinstance(metadata.get("presentation"), dict)
            and metadata["presentation"].get("type") == "tree"
        ):
            metadata["presentation"] = payload

    @classmethod
    def _has_hierarchical_dimensions(
        cls,
        level_fields: list[str],
        profile: PresentationDataProfile,
    ) -> bool:
        field_map = profile.field_map()
        for field_key in level_fields:
            field_profile = field_map.get(field_key)
            if field_profile is None:
                return False
            if not field_profile.is_dimension_candidate and field_profile.semantic_type not in {
                "nominal",
                "ordinal",
                "identifier",
            }:
                return False
        return len(level_fields) >= 1

    @classmethod
    def _tabular_rows(cls, metadata: dict[str, Any]) -> list[dict[str, Any]]:
        return PresentationChartCompilerService._prefer_table_rows(metadata) or (
            PresentationChartCompilerService._tabular_rows(metadata)
        )

    @classmethod
    def _build_nodes_from_rows(
        cls,
        rows: list[dict[str, Any]],
        *,
        level_fields: list[str],
        label_field: str | None,
        badge_field: str | None,
        labels: dict[str, str],
        max_depth: int | None,
    ) -> list[dict[str, Any]]:
        if not level_fields:
            return []

        depth_limit = max_depth if max_depth is not None else len(level_fields)
        roots: dict[str, dict[str, Any]] = {}

        for row in rows:
            if not isinstance(row, dict):
                continue

            path: list[tuple[str, str]] = []
            for field_key in level_fields[:depth_limit]:
                raw = row.get(field_key)
                if raw is None or str(raw).strip() == "":
                    break
                path.append((field_key, str(raw).strip()))
            if not path:
                continue

            cursor = roots
            for depth, (field_key, token) in enumerate(path):
                node_id = f"{field_key}:{token}"
                node = cursor.get(node_id)
                if node is None:
                    label = labels.get(field_key) or token
                    if label_field and depth == len(path) - 1:
                        label = str(row.get(label_field) or label).strip() or label
                    node = {
                        "id": node_id,
                        "label": label,
                        "meta": {"field": field_key, "value": token},
                        "_children": {},
                    }
                    cursor[node_id] = node

                if badge_field and depth == len(path) - 1 and row.get(badge_field) is not None:
                    node["badge"] = str(row.get(badge_field))

                if depth < len(path) - 1:
                    children = node.setdefault("_children", {})
                    if isinstance(children, dict):
                        cursor = children

        return [cls._serialize_tree_node(node) for node in roots.values()]

    @classmethod
    def _serialize_tree_node(cls, node: dict[str, Any]) -> dict[str, Any]:
        payload = {key: value for key, value in node.items() if key != "_children"}
        children = node.get("_children")
        if isinstance(children, dict) and children:
            payload["children"] = [
                cls._serialize_tree_node(child) for child in children.values()
            ]
        return payload
