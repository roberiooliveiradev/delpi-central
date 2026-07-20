import type { FlowchartV1 } from "@delpi/plugin-ui/index";

import type { DecompositionNode, DecompositionTreeV1 } from "../types/decomposition";
import type { DiagramDiff } from "../types/diagram";
import type { RichTreeNode } from "../types/richTree";

/** Remove highlight visual dos nós do flowchart (exibição sem destaque automático). */
export function stripFlowchartHighlights(flowchart: FlowchartV1): FlowchartV1 {
  return {
    ...flowchart,
    nodes: flowchart.nodes.map((node) => {
      if (!("highlight" in node) || node.highlight == null) return node;
      const { highlight: _removed, ...rest } = node;
      return rest;
    }),
  };
}

/**
 * Inclui nós removidos (só na referência) no flowchart de exibição do diff.
 * Não altera o editable — só para preview com «Destacar diferenças».
 */
export function mergeRemovedNodesIntoFlowchartForDiff(
  flowchart: FlowchartV1,
  referenceFlowchart: FlowchartV1 | null | undefined,
  removedIds: string[] | null | undefined,
): FlowchartV1 {
  if (!removedIds?.length || !referenceFlowchart?.nodes?.length) return flowchart;

  const currentIds = new Set(flowchart.nodes.map((node) => node.id));
  const refById = new Map(referenceFlowchart.nodes.map((node) => [node.id, node]));
  const extras = removedIds
    .filter((id) => !currentIds.has(id))
    .map((id) => refById.get(id))
    .filter((node): node is NonNullable<typeof node> => Boolean(node))
    .map((node) => ({
      ...node,
      highlight: "removed" as const,
    }));

  if (!extras.length) return flowchart;

  // Arestas da referência entre nós removidos (ou removido↔vivo) para manter contexto.
  const displayIds = new Set([...currentIds, ...extras.map((n) => n.id)]);
  const currentEdgeIds = new Set((flowchart.edges ?? []).map((e) => e.id));
  const extraEdges = (referenceFlowchart.edges ?? []).filter(
    (edge) =>
      !currentEdgeIds.has(edge.id) &&
      displayIds.has(edge.from) &&
      displayIds.has(edge.to) &&
      (removedIds.includes(edge.from) || removedIds.includes(edge.to)),
  );

  // Lanes da referência que os nós removidos usam e ainda não estão no flowchart.
  const laneIds = new Set((flowchart.lanes ?? []).map((l) => l.id));
  const extraLanes = (referenceFlowchart.lanes ?? []).filter((lane) => {
    if (laneIds.has(lane.id)) return false;
    return extras.some((node) => node.lane_id === lane.id);
  });

  return {
    ...flowchart,
    lanes:
      extraLanes.length > 0
        ? [...(flowchart.lanes ?? []), ...extraLanes]
        : flowchart.lanes,
    nodes: [...flowchart.nodes, ...extras],
    edges: [...(flowchart.edges ?? []), ...extraEdges],
  };
}

export function stripDecompositionHighlights(tree: DecompositionTreeV1): DecompositionTreeV1 {
  return {
    ...tree,
    nodes: tree.nodes.map((node) => {
      if (!node.highlight) return node;
      const { highlight: _removed, ...rest } = node;
      return rest as DecompositionNode;
    }),
  };
}

/**
 * Inclui nós removidos (presentes só na referência) na árvore de exibição do diff.
 * Não altera a árvore editável — só para preview com «Destacar diferenças».
 */
export function mergeRemovedNodesIntoTreeForDiff(
  tree: DecompositionTreeV1,
  referenceTree: DecompositionTreeV1 | null | undefined,
  removedIds: string[] | null | undefined,
): DecompositionTreeV1 {
  if (!removedIds?.length || !referenceTree?.nodes?.length) return tree;

  const currentIds = new Set(tree.nodes.map((node) => node.id));
  const removedSet = new Set(removedIds);
  const refById = new Map(
    referenceTree.nodes.filter((node) => !node.disabled).map((node) => [node.id, node]),
  );

  function resolveParentId(refParentId: string | null | undefined): string | null {
    let parentId = refParentId ?? null;
    while (parentId) {
      if (currentIds.has(parentId) || removedSet.has(parentId)) return parentId;
      parentId = refById.get(parentId)?.parent_id ?? null;
    }
    return null;
  }

  const extras: DecompositionNode[] = [];
  for (const id of removedIds) {
    if (currentIds.has(id)) continue;
    const refNode = refById.get(id);
    if (!refNode) continue;
    extras.push({
      ...refNode,
      parent_id: resolveParentId(refNode.parent_id),
      highlight: "removed",
    });
  }

  if (!extras.length) return tree;
  return { ...tree, nodes: [...tree.nodes, ...extras] };
}

/** Aplica classes de diff (changed/added/removed) sobre a árvore rica. */
export function applyDiffHighlightsToRichTree(
  root: RichTreeNode | null,
  diff: DiagramDiff | null | undefined
): RichTreeNode | null {
  if (!root || !diff) return root;

  const changed = new Set(diff.changed ?? []);
  const added = new Set(diff.added ?? []);
  const removed = new Set(diff.removed ?? []);

  function mapNode(node: RichTreeNode): RichTreeNode {
    let highlight: RichTreeNode["highlight"];
    if (removed.has(node.id)) highlight = "removed";
    else if (added.has(node.id)) highlight = "tobe";
    else if (changed.has(node.id)) highlight = "changed";
    else highlight = undefined;

    return {
      ...node,
      highlight,
      children: node.children?.map(mapNode),
    };
  }

  return mapNode(root);
}

export function formatDiffSummary(
  diff: { changed?: string[]; added?: string[]; removed?: string[] } | null | undefined,
  refLabel?: string | null
): string | null {
  if (!diff) return null;
  const changed = diff.changed?.length ?? 0;
  const added = diff.added?.length ?? 0;
  const removed = diff.removed?.length ?? 0;
  if (!changed && !added && !removed) return null;
  const vs = refLabel ? `vs referência (${refLabel})` : "vs referência";
  return `${vs}: ${changed} alterados, ${added} novos, ${removed} removidos.`;
}
