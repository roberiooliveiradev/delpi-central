import type { ComponenteItem } from "../data/api/maintenanceApi";

export type ComponenteTreeNode = {
  item: ComponenteItem;
  children: ComponenteTreeNode[];
};

/** Monta floresta a partir de lista plana ordenada por `nivel` (1 = raiz). */
export function buildComponentesForest(items: ComponenteItem[]): ComponenteTreeNode[] {
  const roots: ComponenteTreeNode[] = [];
  const stack: ComponenteTreeNode[] = [];

  for (const item of items) {
    const node: ComponenteTreeNode = { item, children: [] };
    const level = Math.max(1, item.nivel);

    if (level === 1) {
      roots.push(node);
    } else {
      const parent = stack[level - 2];
      if (parent) {
        parent.children.push(node);
      } else {
        roots.push(node);
      }
    }

    stack[level - 1] = node;
    stack.length = level;
  }

  return roots;
}

export function countComponenteTreeNodes(nodes: ComponenteTreeNode[]): number {
  return nodes.reduce((total, node) => total + 1 + countComponenteTreeNodes(node.children), 0);
}
