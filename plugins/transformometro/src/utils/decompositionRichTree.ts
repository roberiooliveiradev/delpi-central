import {
  DECOMPOSITION_LEVEL_LABELS,
  type DecompositionLevel,
  type DecompositionNode,
  type DecompositionOverlayV1,
  type DecompositionTreeV1,
} from "../types/decomposition";
import type { RichTreeNode } from "../types/richTree";

const LEVEL_BADGE: Record<DecompositionLevel, string> = {
  processo_chave: "PK",
  tarefa: "T",
  sub_tarefa: "ST",
};

export function countRichTreeNodes(node: RichTreeNode): number {
  const children = node.children ?? [];
  return 1 + children.reduce((sum, child) => sum + countRichTreeNodes(child), 0);
}

function childrenOf(parentId: string | null, nodes: DecompositionNode[]): DecompositionNode[] {
  return nodes
    .filter((node) => (node.parent_id ?? null) === parentId && !node.disabled)
    .sort((a, b) => a.ordem - b.ordem);
}

function resolveNodeLabel(
  node: DecompositionNode,
  override?: NonNullable<DecompositionOverlayV1["node_overrides"]>[string]
): string {
  if (override && override.label !== undefined) {
    return override.label;
  }
  if (node.label !== undefined && node.label !== null) {
    return node.label;
  }
  return DECOMPOSITION_LEVEL_LABELS[node.level];
}

function mapDecompositionNode(
  node: DecompositionNode,
  nodes: DecompositionNode[],
  overlay?: DecompositionOverlayV1
): RichTreeNode {
  const override = overlay?.node_overrides?.[node.id];
  const label = resolveNodeLabel(node, override);
  const subtitle = override?.descricao?.trim() || node.descricao?.trim() || undefined;
  const highlight = override?.highlight ?? node.highlight;
  const childNodes = childrenOf(node.id, nodes).map((child) =>
    mapDecompositionNode(child, nodes, overlay)
  );

  return {
    id: node.id,
    label,
    subtitle,
    badge: LEVEL_BADGE[node.level],
    metaCaption: `Ordem ${node.ordem}`,
    highlight,
    children: childNodes.length ? childNodes : undefined,
  };
}

export function buildDecompositionRichTree(
  tree: DecompositionTreeV1,
  options?: {
    title?: string;
    overlay?: DecompositionOverlayV1;
  }
): RichTreeNode | null {
  const activeNodes = tree.nodes.filter((node) => !node.disabled);
  const roots = childrenOf(null, activeNodes);
  if (!roots.length) return null;

  const mappedRoots = roots.map((node) => mapDecompositionNode(node, activeNodes, options?.overlay));

  if (mappedRoots.length === 1 && !options?.title) {
    return mappedRoots[0];
  }

  return {
    id: "decomposition-root",
    label: options?.title ?? "Mapeamento do processo",
    subtitle: `${activeNodes.length} nó(s) no WBS`,
    children: mappedRoots,
  };
}
