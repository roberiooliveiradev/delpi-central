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
 *
 * Mantém as faixas da referência: casa por id/rótulo com as faixas atuais;
 * se a faixa «de antes» não existir, adiciona-a. Fantasmas vão à direita e
 * com Y alinhado à faixa correta (sem empilhar no fluxo atual).
 */
export function mergeRemovedNodesIntoFlowchartForDiff(
  flowchart: FlowchartV1,
  referenceFlowchart: FlowchartV1 | null | undefined,
  removedIds: string[] | null | undefined,
): FlowchartV1 {
  if (!removedIds?.length || !referenceFlowchart?.nodes?.length) return flowchart;

  const currentIds = new Set(flowchart.nodes.map((node) => node.id));
  const refById = new Map(referenceFlowchart.nodes.map((node) => [node.id, node]));
  const currentLanes = [...(flowchart.lanes ?? [])];
  const refLanes = referenceFlowchart.lanes ?? [];

  const rawExtras = removedIds
    .filter((id) => !currentIds.has(id))
    .map((id) => refById.get(id))
    .filter((node): node is NonNullable<typeof node> => Boolean(node));

  if (!rawExtras.length) return flowchart;

  const lanesToAdd: NonNullable<FlowchartV1["lanes"]> = [];
  const seenAdd = new Set<string>();

  function normalizeLaneLabel(label: string): string {
    return label
      .trim()
      .toLowerCase()
      .replace(/^\d+\s*[—\-:.)]\s*/u, "")
      .replace(/\s+/g, " ");
  }

  function resolveTargetLaneId(refLaneId: string | undefined): string | undefined {
    if (!refLaneId) return currentLanes[0]?.id;
    if (currentLanes.some((lane) => lane.id === refLaneId)) return refLaneId;
    if (lanesToAdd.some((lane) => lane.id === refLaneId)) return refLaneId;

    const refLane = refLanes.find((lane) => lane.id === refLaneId);
    if (!refLane) return currentLanes[0]?.id;

    const refNorm = normalizeLaneLabel(refLane.label);
    const byLabel = currentLanes.find(
      (lane) => normalizeLaneLabel(lane.label) === refNorm,
    );
    if (byLabel) return byLabel.id;

    if (!seenAdd.has(refLane.id)) {
      seenAdd.add(refLane.id);
      lanesToAdd.push({
        ...refLane,
        order: currentLanes.length + lanesToAdd.length,
      });
    }
    return refLane.id;
  }

  const targetLaneIds = rawExtras.map((node) => resolveTargetLaneId(node.lane_id));
  const mergedLanes = [...currentLanes, ...lanesToAdd];

  function laneTopOffset(lanes: NonNullable<FlowchartV1["lanes"]>, laneId: string): number {
    let top = 0;
    for (const lane of lanes) {
      if (lane.id === laneId) return top;
      top += Number(lane.height) > 0 ? Number(lane.height) : 168;
    }
    return 0;
  }

  function localYInLane(
    node: { position: { y: number }; lane_id?: string },
    lanes: NonNullable<FlowchartV1["lanes"]>,
  ): number {
    if (!node.lane_id) return 40;
    return Math.max(28, node.position.y - laneTopOffset(lanes, node.lane_id));
  }

  const currentMaxX = flowchart.nodes.reduce(
    (max, node) => Math.max(max, node.position.x),
    0,
  );
  const extrasMinX = rawExtras.reduce(
    (min, node) => Math.min(min, node.position.x),
    rawExtras[0].position.x,
  );
  const shiftX = Math.max(0, currentMaxX + 280 - extrasMinX);

  const extras = rawExtras.map((node, index) => {
    const targetLaneId = targetLaneIds[index];
    const localY = localYInLane(node, refLanes);
    return {
      ...node,
      lane_id: targetLaneId,
      position: {
        x: node.position.x + shiftX,
        y: (targetLaneId ? laneTopOffset(mergedLanes, targetLaneId) : 0) + localY,
      },
      highlight: "removed" as const,
    };
  });

  const displayIds = new Set([...currentIds, ...extras.map((n) => n.id)]);
  const currentEdgeIds = new Set((flowchart.edges ?? []).map((e) => e.id));
  const extraEdges = (referenceFlowchart.edges ?? []).filter(
    (edge) =>
      !currentEdgeIds.has(edge.id) &&
      displayIds.has(edge.from) &&
      displayIds.has(edge.to) &&
      (removedIds.includes(edge.from) || removedIds.includes(edge.to)),
  );

  return {
    ...flowchart,
    lanes: mergedLanes.length ? mergedLanes : flowchart.lanes,
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
