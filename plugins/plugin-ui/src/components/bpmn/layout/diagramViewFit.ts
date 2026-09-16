import type { FitViewOptions, Node } from "@xyflow/react";

import {
  contentBoundsFromFlowNodes,
  DIAGRAM_FIT_MAX_ZOOM,
  DIAGRAM_FIT_PADDING,
  DIAGRAM_ZOOM_MAX,
  DIAGRAM_ZOOM_MIN,
} from "./diagramViewport";

export { contentBoundsFromFlowNodes } from "./diagramViewport";
export { DIAGRAM_ZOOM_MAX, DIAGRAM_ZOOM_MIN } from "./diagramViewport";

export const DIAGRAM_FIT_VIEW_OPTIONS: FitViewOptions = {
  padding: DIAGRAM_FIT_PADDING,
  duration: 0,
  minZoom: DIAGRAM_ZOOM_MIN,
  maxZoom: DIAGRAM_FIT_MAX_ZOOM,
};

export const DIAGRAM_USER_ZOOM_EXTENT = {
  minZoom: DIAGRAM_ZOOM_MIN,
  maxZoom: DIAGRAM_ZOOM_MAX,
} as const;

/**
 * Enquadra nós de atividade no espaço WORLD.
 * Cabeçalhos de faixa ficam de fora: a largura visual da raia segue os filhos
 * e, se entrar no fit, o zoom despenca (~8%) mesmo com o grafo compacto.
 */
export function getDiagramFitNodes(nodes: Node[]): Node[] {
  const activityNodes = nodes.filter((node) => node.type !== "lane");
  return activityNodes.length ? activityNodes : nodes;
}

/** Exportação PNG inclui cabeçalhos de faixa e altura total das swimlanes. */
export function getDiagramExportNodes(nodes: Node[]): Node[] {
  if (nodes.some((node) => node.type === "lane")) {
    return nodes;
  }
  return getDiagramFitNodes(nodes);
}

export function fitBoundsFromDiagramNodes(nodes: Node[]) {
  return contentBoundsFromFlowNodes(getDiagramFitNodes(nodes));
}
