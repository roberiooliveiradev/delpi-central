from __future__ import annotations

import copy
from typing import Any

from tm_app.domain.decomposition.decomposition_tree_v1 import (
    DecompositionValidationError,
    empty_escopo,
    empty_overlay,
    empty_tree,
    expand_escopo_node_ids,
    tree_node_ids,
    validate_decomposition_escopo,
    validate_decomposition_overlay_v1,
    validate_decomposition_tree_v1,
)


class RevisaoDecomposicaoMergeService:
    def merge(
        self,
        *,
        tree: dict[str, Any] | None,
        escopo: dict[str, Any] | None,
        overlay: dict[str, Any] | None,
    ) -> dict[str, Any]:
        base = copy.deepcopy(validate_decomposition_tree_v1(tree or empty_tree()))
        scope = validate_decomposition_escopo(
            escopo or empty_escopo(),
            tree_node_ids_set=tree_node_ids(base),
        )
        overlay_doc = validate_decomposition_overlay_v1(overlay or empty_overlay())

        allowed = expand_escopo_node_ids(base, scope)
        scoped_nodes = [
            node
            for node in base.get("nodes", [])
            if isinstance(node, dict) and str(node.get("id")) in allowed
        ]
        scoped = {**base, "nodes": scoped_nodes}
        merged_nodes = self._apply_overlay(scoped, overlay_doc)
        warnings = self._collect_warnings(base, scope, overlay_doc, allowed)

        return {
            "tree": {**scoped, "nodes": merged_nodes},
            "escopo": scope,
            "overlay": overlay_doc,
            "warnings": warnings,
        }

    def assert_overlay_within_escopo(
        self,
        *,
        tree: dict[str, Any] | None,
        escopo: dict[str, Any] | None,
        overlay: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Valida overlay e garante que todos os IDs tocados estão no escopo expandido."""
        base = validate_decomposition_tree_v1(tree or empty_tree())
        scope = validate_decomposition_escopo(
            escopo or empty_escopo(),
            tree_node_ids_set=tree_node_ids(base),
        )
        overlay_doc = validate_decomposition_overlay_v1(overlay or empty_overlay())
        allowed = expand_escopo_node_ids(base, scope)
        outside: list[str] = []
        for node_id in overlay_doc.get("node_overrides") or {}:
            if str(node_id) not in allowed:
                outside.append(str(node_id))
        for node_id in overlay_doc.get("disabled_node_ids") or []:
            if str(node_id) not in allowed:
                outside.append(str(node_id))
        if outside:
            unique = sorted(set(outside))
            raise DecompositionValidationError(
                "Overlay fora do escopo da melhoria: " + ", ".join(unique[:8])
                + ("…" if len(unique) > 8 else "")
                + ". Ajuste o Escopo no mapeamento ou remova esses nós do overlay."
            )
        return overlay_doc

    def diff_highlights(
        self,
        *,
        baseline: dict[str, Any] | None,
        current: dict[str, Any] | None,
    ) -> dict[str, Any]:
        baseline_nodes = {
            str(node["id"]): node
            for node in (baseline or empty_tree()).get("nodes", [])
            if isinstance(node, dict) and node.get("id")
        }
        current_nodes = {
            str(node["id"]): node
            for node in (current or empty_tree()).get("nodes", [])
            if isinstance(node, dict) and node.get("id")
        }

        changed: list[str] = []
        added: list[str] = []
        removed: list[str] = []

        for node_id, node in current_nodes.items():
            if node_id not in baseline_nodes:
                added.append(node_id)
            elif str(node.get("label")) != str(baseline_nodes[node_id].get("label")):
                changed.append(node_id)

        for node_id in baseline_nodes:
            if node_id not in current_nodes:
                removed.append(node_id)

        return {"changed": changed, "added": added, "removed": removed}

    def _apply_overlay(
        self,
        scoped: dict[str, Any],
        overlay: dict[str, Any],
    ) -> list[dict[str, Any]]:
        disabled = set(overlay.get("disabled_node_ids") or [])
        overrides = overlay.get("node_overrides") or {}
        nodes: list[dict[str, Any]] = []

        for node in scoped.get("nodes", []):
            if not isinstance(node, dict):
                continue
            node_id = str(node.get("id") or "")
            if node_id in disabled:
                continue
            merged = copy.deepcopy(node)
            override = overrides.get(node_id)
            if isinstance(override, dict):
                if override.get("label"):
                    merged["label"] = override["label"]
                if "descricao" in override:
                    merged["descricao"] = override["descricao"]
                if override.get("highlight"):
                    merged["highlight"] = override["highlight"]
                if override.get("meta"):
                    merged["meta"] = {**(merged.get("meta") or {}), **override["meta"]}
            nodes.append(merged)

        return nodes

    def _collect_warnings(
        self,
        tree: dict[str, Any],
        escopo: dict[str, Any],
        overlay: dict[str, Any],
        allowed: set[str],
    ) -> list[str]:
        warnings: list[str] = []
        all_ids = tree_node_ids(tree)
        if not escopo.get("inherit_all", True):
            missing = [node_id for node_id in (escopo.get("node_ids") or []) if node_id not in all_ids]
            if missing:
                warnings.append(f"Escopo referencia nós inexistentes: {', '.join(missing[:3])}.")
        for node_id in overlay.get("node_overrides") or {}:
            if node_id not in allowed:
                warnings.append(f"Overlay referencia nó fora do escopo: {node_id}.")
        return warnings
