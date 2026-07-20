from __future__ import annotations

import re
from typing import Any

TREE_FORMAT = "decomposition_tree_v1"
OVERLAY_FORMAT = "decomposition_overlay_v1"
CONTEXT_FORMAT = "instancia_contexto_v1"
FORMAT_VERSION = 1

MAX_NODES = 500
MAX_PROCESSO_CHAVE = 50

NODE_LEVELS = frozenset({"processo_chave", "tarefa", "sub_tarefa"})
LEVEL_PARENT: dict[str, str | None] = {
    "processo_chave": None,
    "tarefa": "processo_chave",
    "sub_tarefa": "tarefa",
}

NODE_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_\-]{1,64}$")
HIGHLIGHTS = frozenset({"asis", "tobe", "changed", "removed"})


class DecompositionValidationError(ValueError):
    pass


def empty_tree() -> dict[str, Any]:
    return {
        "format": TREE_FORMAT,
        "format_version": FORMAT_VERSION,
        "nodes": [],
    }


def empty_overlay() -> dict[str, Any]:
    return {
        "format": OVERLAY_FORMAT,
        "format_version": FORMAT_VERSION,
        "node_overrides": {},
        "disabled_node_ids": [],
        "extra_nodes": [],
    }


def empty_escopo() -> dict[str, Any]:
    return {
        "node_ids": [],
        "inherit_all": True,
        "include_descendants": True,
    }


def empty_contexto() -> dict[str, Any]:
    return {
        "format": CONTEXT_FORMAT,
        "format_version": FORMAT_VERSION,
        "observacoes_rollout": None,
        "responsavel_local": None,
        "contato": None,
        "node_notes": {},
        "links": [],
        "meta": {},
    }


def _require_dict(value: Any, label: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise DecompositionValidationError(f"{label} deve ser um objeto.")
    return value


def tree_node_ids(tree: dict[str, Any]) -> set[str]:
    return {
        str(node["id"])
        for node in tree.get("nodes", [])
        if isinstance(node, dict) and node.get("id") and not node.get("disabled")
    }


def _validate_node(node: Any, *, index: int) -> None:
    if not isinstance(node, dict):
        raise DecompositionValidationError(f"nodes[{index}] deve ser um objeto.")
    node_id = node.get("id")
    if not isinstance(node_id, str) or not NODE_ID_PATTERN.match(node_id):
        raise DecompositionValidationError(f"nodes[{index}].id inválido.")
    level = node.get("level")
    if level not in NODE_LEVELS:
        raise DecompositionValidationError(f"nodes[{index}].level inválido: {level!r}.")
    ordem = node.get("ordem")
    if not isinstance(ordem, int) or ordem < 1 or ordem > 999:
        raise DecompositionValidationError(f"nodes[{index}].ordem inválida.")
    label = node.get("label")
    if not isinstance(label, str) or not label.strip():
        raise DecompositionValidationError(f"nodes[{index}].label obrigatório.")
    parent_id = node.get("parent_id")
    if parent_id is not None and (
        not isinstance(parent_id, str) or not NODE_ID_PATTERN.match(parent_id)
    ):
        raise DecompositionValidationError(f"nodes[{index}].parent_id inválido.")
    descricao = node.get("descricao")
    if descricao is not None and not isinstance(descricao, str):
        raise DecompositionValidationError(f"nodes[{index}].descricao inválida.")
    disabled = node.get("disabled", False)
    if disabled is not None and not isinstance(disabled, bool):
        raise DecompositionValidationError(f"nodes[{index}].disabled inválido.")


def validate_decomposition_tree_v1(doc: Any) -> dict[str, Any]:
    data = _require_dict(doc, "decomposição")
    if data.get("format") != TREE_FORMAT:
        raise DecompositionValidationError("format deve ser decomposition_tree_v1.")
    if data.get("format_version") != FORMAT_VERSION:
        raise DecompositionValidationError("format_version inválida.")

    nodes = data.get("nodes")
    if not isinstance(nodes, list):
        raise DecompositionValidationError("nodes deve ser uma lista.")
    if len(nodes) > MAX_NODES:
        raise DecompositionValidationError(f"Máximo de {MAX_NODES} nós.")

    seen_ids: set[str] = set()
    by_id: dict[str, dict[str, Any]] = {}
    for index, node in enumerate(nodes):
        _validate_node(node, index=index)
        node_id = str(node["id"])
        if node_id in seen_ids:
            raise DecompositionValidationError(f"node_id duplicado: {node_id}.")
        seen_ids.add(node_id)
        by_id[node_id] = node

    pk_count = 0
    sibling_orders: dict[str | None, set[int]] = {}
    for node in nodes:
        level = str(node["level"])
        parent_id = node.get("parent_id")
        if level == "processo_chave":
            pk_count += 1
            if parent_id is not None:
                raise DecompositionValidationError(
                    f"processo_chave {node['id']} não pode ter parent_id."
                )
        else:
            if not isinstance(parent_id, str) or parent_id not in by_id:
                raise DecompositionValidationError(
                    f"nó {node['id']}: parent_id inválido ou inexistente."
                )
            parent = by_id[parent_id]
            expected_parent_level = LEVEL_PARENT.get(level)
            if expected_parent_level and str(parent.get("level")) != expected_parent_level:
                if not (
                    level == "sub_tarefa"
                    and str(parent.get("level")) == "processo_chave"
                ):
                    raise DecompositionValidationError(
                        f"nó {node['id']}: level {level} incompatível com pai {parent_id}."
                    )

        parent_key = str(parent_id) if parent_id else None
        ordem = int(node["ordem"])
        sibling_orders.setdefault(parent_key, set())
        if ordem in sibling_orders[parent_key]:
            raise DecompositionValidationError(
                f"ordem duplicada entre irmãos (parent={parent_key!r}, ordem={ordem})."
            )
        sibling_orders[parent_key].add(ordem)

    if pk_count > MAX_PROCESSO_CHAVE:
        raise DecompositionValidationError(f"Máximo de {MAX_PROCESSO_CHAVE} processos-chave.")

    return data


def validate_decomposition_overlay_v1(doc: Any) -> dict[str, Any]:
    data = _require_dict(doc, "overlay")
    if data.get("format") != OVERLAY_FORMAT:
        raise DecompositionValidationError("format deve ser decomposition_overlay_v1.")
    if data.get("format_version") != FORMAT_VERSION:
        raise DecompositionValidationError("format_version inválida.")

    node_overrides = data.get("node_overrides", {})
    if not isinstance(node_overrides, dict):
        raise DecompositionValidationError("node_overrides deve ser objeto.")

    for node_id, override in node_overrides.items():
        if not isinstance(node_id, str) or not NODE_ID_PATTERN.match(node_id):
            raise DecompositionValidationError(f"node_overrides[{node_id!r}] id inválido.")
        if not isinstance(override, dict):
            raise DecompositionValidationError(f"node_overrides[{node_id}] deve ser objeto.")
        highlight = override.get("highlight")
        if highlight is not None and highlight not in HIGHLIGHTS:
            raise DecompositionValidationError(f"highlight inválido em {node_id}.")
        if "parent_id" in override:
            parent_id = override.get("parent_id")
            if parent_id is not None and (
                not isinstance(parent_id, str) or not NODE_ID_PATTERN.match(parent_id)
            ):
                raise DecompositionValidationError(
                    f"node_overrides[{node_id}].parent_id inválido."
                )
        if "ordem" in override:
            ordem = override.get("ordem")
            if not isinstance(ordem, int) or ordem < 1 or ordem > 999:
                raise DecompositionValidationError(
                    f"node_overrides[{node_id}].ordem inválida."
                )

    disabled = data.get("disabled_node_ids", [])
    if not isinstance(disabled, list) or not all(isinstance(x, str) for x in disabled):
        raise DecompositionValidationError("disabled_node_ids inválido.")

    extra_nodes = data.get("extra_nodes", [])
    if not isinstance(extra_nodes, list):
        raise DecompositionValidationError("extra_nodes deve ser uma lista.")
    if len(extra_nodes) > MAX_NODES:
        raise DecompositionValidationError(f"Máximo de {MAX_NODES} extra_nodes.")

    seen_extra: set[str] = set()
    for index, node in enumerate(extra_nodes):
        _validate_node(node, index=index)
        node_id = str(node["id"])
        if node_id in seen_extra:
            raise DecompositionValidationError(f"extra_nodes id duplicado: {node_id}.")
        seen_extra.add(node_id)
        highlight = node.get("highlight")
        if highlight is not None and highlight not in HIGHLIGHTS:
            raise DecompositionValidationError(f"extra_nodes[{node_id}].highlight inválido.")

    return {
        **data,
        "node_overrides": node_overrides,
        "disabled_node_ids": list(disabled),
        "extra_nodes": list(extra_nodes),
    }


def normalize_sibling_ordens(nodes: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Reatribui ordem 1..n por parent para evitar colisões após merge/composição."""
    by_parent: dict[str | None, list[dict[str, Any]]] = {}
    for node in nodes:
        if not isinstance(node, dict) or not node.get("id"):
            continue
        parent_key = str(node["parent_id"]) if node.get("parent_id") else None
        by_parent.setdefault(parent_key, []).append(node)

    result: list[dict[str, Any]] = []
    for group in by_parent.values():
        group.sort(key=lambda n: (int(n.get("ordem") or 1), str(n.get("id") or "")))
        for index, node in enumerate(group, start=1):
            updated = dict(node)
            updated["ordem"] = index
            result.append(updated)
    return result


def validate_decomposition_escopo(
    doc: Any,
    *,
    tree_node_ids_set: set[str] | None = None,
) -> dict[str, Any]:
    data = _require_dict(doc, "escopo")
    node_ids = data.get("node_ids", [])
    if not isinstance(node_ids, list) or not all(isinstance(x, str) for x in node_ids):
        raise DecompositionValidationError("node_ids inválido.")
    inherit_all = data.get("inherit_all", True)
    if not isinstance(inherit_all, bool):
        raise DecompositionValidationError("inherit_all inválido.")
    include_descendants = data.get("include_descendants", True)
    if not isinstance(include_descendants, bool):
        raise DecompositionValidationError("include_descendants inválido.")

    if tree_node_ids_set is not None and not inherit_all:
        invalid = [node_id for node_id in node_ids if node_id not in tree_node_ids_set]
        if invalid:
            raise DecompositionValidationError(
                f"node_ids fora da árvore: {', '.join(invalid[:5])}."
            )

    return {
        "node_ids": list(node_ids),
        "inherit_all": inherit_all,
        "include_descendants": include_descendants,
    }


def validate_instancia_contexto_v1(doc: Any) -> dict[str, Any]:
    data = _require_dict(doc, "contexto")
    if data.get("format") != CONTEXT_FORMAT:
        raise DecompositionValidationError("format deve ser instancia_contexto_v1.")
    if data.get("format_version") != FORMAT_VERSION:
        raise DecompositionValidationError("format_version inválida.")

    node_notes = data.get("node_notes", {})
    if not isinstance(node_notes, dict):
        raise DecompositionValidationError("node_notes inválido.")

    links = data.get("links", [])
    if not isinstance(links, list):
        raise DecompositionValidationError("links inválido.")

    return data


def expand_escopo_node_ids(
    tree: dict[str, Any],
    escopo: dict[str, Any],
) -> set[str]:
    """Expande escopo com descendentes quando include_descendants=true."""
    if escopo.get("inherit_all", True):
        return tree_node_ids(tree)

    selected = set(escopo.get("node_ids") or [])
    if not selected:
        return set()

    if not escopo.get("include_descendants", True):
        return selected

    nodes = [n for n in tree.get("nodes", []) if isinstance(n, dict)]
    children: dict[str, list[str]] = {}
    for node in nodes:
        parent = node.get("parent_id")
        if parent:
            children.setdefault(str(parent), []).append(str(node["id"]))

    expanded = set(selected)
    stack = list(selected)
    while stack:
        current = stack.pop()
        for child_id in children.get(current, []):
            if child_id not in expanded:
                expanded.add(child_id)
                stack.append(child_id)
    return expanded
