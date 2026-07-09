import type { FitViewOptions, Node } from "@xyflow/react";

export const DIAGRAM_FIT_VIEW_OPTIONS: FitViewOptions = {
  padding: 0.18,
  duration: 0,
  minZoom: 0.12,
  maxZoom: 1.35,
};

/** Faixas ocupam 2400px de largura — excluir do enquadramento para centralizar o conteúdo. */
export function getDiagramFitNodes(nodes: Node[]): Node[] {
  const activityNodes = nodes.filter((node) => node.type !== "lane");
  return activityNodes.length ? activityNodes : nodes;
}
