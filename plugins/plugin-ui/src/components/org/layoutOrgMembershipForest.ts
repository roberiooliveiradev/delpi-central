/**
 * Layout hierárquico local (floresta): raízes sem pai no topo;
 * filhos centrados sob o pai. Sem dagre/elkjs.
 */

export type ForestLayoutNode = { id: string };

export type ForestLayoutEdge = { source: string; target: string };

export type ForestLayoutPosition = { x: number; y: number };

export const ORG_MEMBERSHIP_NODE_WIDTH = 240;
export const ORG_MEMBERSHIP_NODE_HEIGHT = 76;
export const ORG_MEMBERSHIP_H_GAP = 48;
export const ORG_MEMBERSHIP_V_GAP = 96;

export function layoutOrgMembershipForest(
  nodes: readonly ForestLayoutNode[],
  edges: readonly ForestLayoutEdge[],
): Map<string, ForestLayoutPosition> {
  const ids = new Set(nodes.map((node) => node.id));
  const children = new Map<string, string[]>();
  const parentOf = new Map<string, string>();

  for (const edge of edges) {
    if (!ids.has(edge.source) || !ids.has(edge.target)) continue;
    if (parentOf.has(edge.target)) continue;
    const list = children.get(edge.source) ?? [];
    list.push(edge.target);
    children.set(edge.source, list);
    parentOf.set(edge.target, edge.source);
  }

  const roots = nodes.map((node) => node.id).filter((id) => !parentOf.has(id));

  const widthCache = new Map<string, number>();
  function subtreeWidth(id: string): number {
    const cached = widthCache.get(id);
    if (cached != null) return cached;
    const kids = children.get(id) ?? [];
    let width = ORG_MEMBERSHIP_NODE_WIDTH;
    if (kids.length > 0) {
      const sum =
        kids.reduce((acc, kid) => acc + subtreeWidth(kid), 0) +
        ORG_MEMBERSHIP_H_GAP * (kids.length - 1);
      width = Math.max(ORG_MEMBERSHIP_NODE_WIDTH, sum);
    }
    widthCache.set(id, width);
    return width;
  }

  const positions = new Map<string, ForestLayoutPosition>();

  function place(id: string, left: number, depth: number): void {
    const width = subtreeWidth(id);
    const kids = children.get(id) ?? [];
    positions.set(id, {
      x: left + width / 2 - ORG_MEMBERSHIP_NODE_WIDTH / 2,
      y: depth * (ORG_MEMBERSHIP_NODE_HEIGHT + ORG_MEMBERSHIP_V_GAP),
    });
    let cursor = left;
    for (const kid of kids) {
      const kidWidth = subtreeWidth(kid);
      place(kid, cursor, depth + 1);
      cursor += kidWidth + ORG_MEMBERSHIP_H_GAP;
    }
  }

  let forestCursor = 0;
  for (const root of roots) {
    const width = subtreeWidth(root);
    place(root, forestCursor, 0);
    forestCursor += width + ORG_MEMBERSHIP_H_GAP * 2;
  }

  for (const node of nodes) {
    if (!positions.has(node.id)) {
      positions.set(node.id, { x: forestCursor, y: 0 });
      forestCursor += ORG_MEMBERSHIP_NODE_WIDTH + ORG_MEMBERSHIP_H_GAP;
    }
  }

  return positions;
}
