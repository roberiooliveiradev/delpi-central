import type { DecompositionNode } from "../types/decomposition";

export type DropPosition = "before" | "after" | "inside";

export const DECOMPOSITION_ROOT_ID = "decomposition-root";

export function getActiveSiblings(
  nodes: DecompositionNode[],
  parentId: string | null,
  excludeId?: string
): DecompositionNode[] {
  return nodes
    .filter(
      (node) =>
        !node.disabled && (node.parent_id ?? null) === parentId && node.id !== excludeId
    )
    .sort((a, b) => a.ordem - b.ordem);
}

export function isDecompositionDescendant(
  nodes: DecompositionNode[],
  ancestorId: string,
  nodeId: string
): boolean {
  const byId = new Map(nodes.map((node) => [node.id, node]));
  let current: string | null = nodeId;

  while (current) {
    if (current === ancestorId) return true;
    const node = byId.get(current);
    current = node?.parent_id ?? null;
  }

  return false;
}

export function canBeDecompositionParent(
  parent: DecompositionNode,
  child: DecompositionNode
): boolean {
  if (child.level === "processo_chave") return false;
  if (child.level === "tarefa") return parent.level === "processo_chave";
  if (child.level === "sub_tarefa") {
    return parent.level === "tarefa" || parent.level === "processo_chave";
  }
  return false;
}

export function canAcceptDecompositionDrop(
  nodes: DecompositionNode[],
  draggedId: string,
  targetId: string,
  position: DropPosition
): boolean {
  if (draggedId === targetId) return false;

  const dragged = nodes.find((node) => node.id === draggedId);
  if (!dragged || dragged.disabled) return false;

  if (targetId === DECOMPOSITION_ROOT_ID) {
    return (
      dragged.level === "processo_chave" &&
      (position === "before" || position === "after")
    );
  }

  const target = nodes.find((node) => node.id === targetId);
  if (!target || target.disabled) return false;
  if (isDecompositionDescendant(nodes, draggedId, targetId)) return false;

  if (position === "inside") {
    return canBeDecompositionParent(target, dragged);
  }

  const newParentId = target.parent_id ?? null;
  if (dragged.level === "processo_chave") {
    return newParentId === null;
  }
  if (newParentId === null) return false;

  const parent = nodes.find((node) => node.id === newParentId);
  return parent ? canBeDecompositionParent(parent, dragged) : false;
}

function applySiblingOrder(
  nodes: DecompositionNode[],
  parentId: string | null,
  orderedIds: string[]
): DecompositionNode[] {
  const ordemById = new Map(orderedIds.map((id, index) => [id, index + 1]));
  return nodes.map((node) => {
    if ((node.parent_id ?? null) === parentId && ordemById.has(node.id)) {
      return { ...node, ordem: ordemById.get(node.id)! };
    }
    return node;
  });
}

export function moveDecompositionNode(
  nodes: DecompositionNode[],
  draggedId: string,
  targetId: string,
  position: DropPosition
): DecompositionNode[] {
  if (!canAcceptDecompositionDrop(nodes, draggedId, targetId, position)) {
    return nodes;
  }

  const dragged = nodes.find((node) => node.id === draggedId);
  if (!dragged) return nodes;

  const oldParentId = dragged.parent_id ?? null;
  let newParentId: string | null;
  let orderedSiblingIds: string[];

  if (targetId === DECOMPOSITION_ROOT_ID) {
    newParentId = null;
    orderedSiblingIds = getActiveSiblings(nodes, null, draggedId).map((node) => node.id);
    if (position === "before") {
      orderedSiblingIds.unshift(draggedId);
    } else {
      orderedSiblingIds.push(draggedId);
    }
  } else {
    const target = nodes.find((node) => node.id === targetId);
    if (!target) return nodes;

    if (position === "inside") {
      newParentId = target.id;
      orderedSiblingIds = [
        ...getActiveSiblings(nodes, newParentId, draggedId).map((node) => node.id),
        draggedId,
      ];
    } else {
      newParentId = target.parent_id ?? null;
      const siblings = getActiveSiblings(nodes, newParentId, draggedId);
      const targetIndex = siblings.findIndex((node) => node.id === targetId);
      const insertIndex = position === "before" ? targetIndex : targetIndex + 1;
      orderedSiblingIds = siblings.map((node) => node.id);
      orderedSiblingIds.splice(insertIndex, 0, draggedId);
    }
  }

  let nextNodes = nodes.map((node) => {
    if (node.id !== draggedId) return node;
    return {
      ...node,
      parent_id: dragged.level === "processo_chave" ? null : newParentId,
    };
  });

  nextNodes = applySiblingOrder(nextNodes, newParentId, orderedSiblingIds);

  if (oldParentId !== newParentId) {
    const oldSiblingIds = getActiveSiblings(nextNodes, oldParentId, draggedId).map(
      (node) => node.id
    );
    nextNodes = applySiblingOrder(nextNodes, oldParentId, oldSiblingIds);
  }

  return nextNodes;
}

export function resolveDecompositionDropPosition(
  offsetY: number,
  rowHeight: number,
  canDropInside: boolean
): DropPosition {
  if (rowHeight <= 0) return "after";
  const ratio = offsetY / rowHeight;

  if (canDropInside && ratio > 0.3 && ratio < 0.7) {
    return "inside";
  }
  return ratio < 0.5 ? "before" : "after";
}
