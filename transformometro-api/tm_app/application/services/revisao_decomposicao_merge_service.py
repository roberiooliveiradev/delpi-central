from __future__ import annotations

import copy
from typing import Any

from tm_app.domain.decomposition.decomposition_tree_v1 import (
    DecompositionValidationError,
    empty_escopo,
    empty_overlay,
    empty_tree,
    expand_escopo_node_ids,
    normalize_sibling_ordens,
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
        tree_base = {**base, "nodes": copy.deepcopy(scoped_nodes)}
        merged_nodes = self.apply_overlay_to_nodes(
            scoped_nodes,
            overlay_doc,
            allowed_base_ids=allowed,
        )
        warnings = self._collect_warnings(base, scope, overlay_doc, allowed)

        return {
            "tree": {**base, "nodes": merged_nodes},
            "tree_base": tree_base,
            "escopo": scope,
            "overlay": overlay_doc,
            "warnings": warnings,
        }

    def apply_overlay_to_nodes(
        self,
        nodes: list[dict[str, Any]],
        overlay: dict[str, Any],
        *,
        allowed_base_ids: set[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Aplica overrides, disables e extra_nodes; normaliza ordem entre irmãos."""
        overlay_doc = validate_decomposition_overlay_v1(overlay or empty_overlay())
        disabled = set(overlay_doc.get("disabled_node_ids") or [])
        overrides = overlay_doc.get("node_overrides") or {}
        allowed = allowed_base_ids

        result: list[dict[str, Any]] = []
        for node in nodes:
            if not isinstance(node, dict):
                continue
            node_id = str(node.get("id") or "")
            if node_id in disabled:
                if allowed is not None and node_id not in allowed:
                    result.append(copy.deepcopy(node))
                    continue
                continue
            merged = copy.deepcopy(node)
            override = overrides.get(node_id)
            if isinstance(override, dict) and (allowed is None or node_id in allowed):
                if override.get("label"):
                    merged["label"] = override["label"]
                if "descricao" in override:
                    merged["descricao"] = override["descricao"]
                if "parent_id" in override:
                    merged["parent_id"] = override.get("parent_id")
                if "ordem" in override and isinstance(override.get("ordem"), int):
                    merged["ordem"] = override["ordem"]
                if override.get("highlight"):
                    merged["highlight"] = override["highlight"]
                if override.get("meta"):
                    merged["meta"] = {**(merged.get("meta") or {}), **override["meta"]}
            result.append(merged)

        existing_ids = {str(n.get("id")) for n in result if n.get("id")}
        for extra in overlay_doc.get("extra_nodes") or []:
            if not isinstance(extra, dict) or not extra.get("id"):
                continue
            extra_id = str(extra["id"])
            if extra_id in existing_ids:
                continue
            added = copy.deepcopy(extra)
            if not added.get("highlight"):
                added["highlight"] = "tobe"
            result.append(added)
            existing_ids.add(extra_id)

        return normalize_sibling_ordens(result)

    def assert_overlay_within_escopo(
        self,
        *,
        tree: dict[str, Any] | None,
        escopo: dict[str, Any] | None,
        overlay: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Valida overlay estrutural e garante escopo (overrides/disable + extras)."""
        base = validate_decomposition_tree_v1(tree or empty_tree())
        scope = validate_decomposition_escopo(
            escopo or empty_escopo(),
            tree_node_ids_set=tree_node_ids(base),
        )
        overlay_doc = validate_decomposition_overlay_v1(overlay or empty_overlay())
        allowed = expand_escopo_node_ids(base, scope)
        base_ids = tree_node_ids(base)
        extra_nodes = overlay_doc.get("extra_nodes") or []
        extra_ids = {str(n["id"]) for n in extra_nodes if isinstance(n, dict) and n.get("id")}
        parent_universe = allowed | extra_ids

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

        for node_id, override in (overlay_doc.get("node_overrides") or {}).items():
            if not isinstance(override, dict) or "parent_id" not in override:
                continue
            parent_id = override.get("parent_id")
            if parent_id is None:
                continue
            if str(parent_id) not in parent_universe:
                raise DecompositionValidationError(
                    f"Reparent de {node_id} para {parent_id} fora do escopo/extras."
                )

        for extra in extra_nodes:
            if not isinstance(extra, dict):
                continue
            extra_id = str(extra.get("id") or "")
            if extra_id in base_ids:
                raise DecompositionValidationError(
                    f"extra_nodes não pode redefinir nó da base: {extra_id}."
                )
            level = str(extra.get("level") or "")
            parent_id = extra.get("parent_id")
            if level == "processo_chave":
                if parent_id is not None:
                    raise DecompositionValidationError(
                        f"extra_nodes {extra_id}: processo-chave não pode ter parent_id."
                    )
                if not scope.get("inherit_all", True):
                    raise DecompositionValidationError(
                        "Só é permitido criar processo-chave no delta quando o escopo "
                        "da melhoria cobre o macro inteiro (inherit_all)."
                    )
            else:
                if not isinstance(parent_id, str) or parent_id not in parent_universe:
                    raise DecompositionValidationError(
                        f"extra_nodes {extra_id}: parent_id deve estar no escopo ou em extras."
                    )

        # Garante árvore resultante válida (níveis/pais)
        try:
            merged_nodes = self.apply_overlay_to_nodes(
                [
                    n
                    for n in base.get("nodes", [])
                    if isinstance(n, dict) and str(n.get("id")) in allowed
                ],
                overlay_doc,
                allowed_base_ids=allowed,
            )
            validate_decomposition_tree_v1({**base, "nodes": merged_nodes})
        except DecompositionValidationError as exc:
            raise DecompositionValidationError(
                f"Delta estrutural inválido após merge: {exc}"
            ) from exc

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
            elif (
                str(node.get("label")) != str(baseline_nodes[node_id].get("label"))
                or (node.get("parent_id") or None)
                != (baseline_nodes[node_id].get("parent_id") or None)
            ):
                changed.append(node_id)

        for node_id in baseline_nodes:
            if node_id not in current_nodes:
                removed.append(node_id)

        return {"changed": changed, "added": added, "removed": removed}

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
        for node_id in overlay.get("disabled_node_ids") or []:
            if node_id not in allowed:
                warnings.append(f"Disable fora do escopo: {node_id}.")
        return warnings
