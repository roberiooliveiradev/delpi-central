import {
  emptyDecompositionOverlay,
  type DecompositionNode,
  type DecompositionOverlayV1,
  type DecompositionTreeV1,
} from "../types/decomposition";

function sameParent(a: DecompositionNode, b: DecompositionNode): boolean {
  return (a.parent_id ?? null) === (b.parent_id ?? null);
}

/**
 * Diff entre árvore base (escopo sem overlay) e árvore editada → overlay estrutural.
 * Playbook 23 Fase D+.
 */
export function decompositionTreeToOverlay(
  base: DecompositionTreeV1,
  edited: DecompositionTreeV1
): DecompositionOverlayV1 {
  const baseById = new Map(base.nodes.map((node) => [node.id, node]));
  const editedById = new Map(edited.nodes.map((node) => [node.id, node]));

  const node_overrides: NonNullable<DecompositionOverlayV1["node_overrides"]> = {};
  const disabled_node_ids: string[] = [];
  const extra_nodes: DecompositionNode[] = [];

  for (const [id, baseNode] of baseById) {
    const editedNode = editedById.get(id);
    if (!editedNode) {
      disabled_node_ids.push(id);
      continue;
    }

    const override: NonNullable<DecompositionOverlayV1["node_overrides"]>[string] = {};
    if ((editedNode.label ?? "").trim() !== (baseNode.label ?? "").trim()) {
      override.label = editedNode.label;
    }
    if ((editedNode.descricao ?? null) !== (baseNode.descricao ?? null)) {
      override.descricao = editedNode.descricao ?? null;
    }
    if (!sameParent(editedNode, baseNode)) {
      override.parent_id = editedNode.parent_id ?? null;
    }
    if (editedNode.ordem !== baseNode.ordem) {
      override.ordem = editedNode.ordem;
    }
    if (Object.keys(override).length > 0) {
      override.highlight = editedNode.highlight ?? "tobe";
      node_overrides[id] = override;
    } else if (editedNode.highlight && editedNode.highlight !== baseNode.highlight) {
      node_overrides[id] = { highlight: editedNode.highlight };
    }
  }

  for (const [id, editedNode] of editedById) {
    if (baseById.has(id)) continue;
    extra_nodes.push({
      ...editedNode,
      highlight: editedNode.highlight ?? "tobe",
    });
  }

  return {
    ...emptyDecompositionOverlay(),
    node_overrides,
    disabled_node_ids,
    extra_nodes,
  };
}
