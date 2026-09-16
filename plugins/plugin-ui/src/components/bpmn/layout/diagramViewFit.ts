import type { FitViewOptions, Node } from "@xyflow/react";

import {
  DIAGRAM_FIT_PADDING,
  DIAGRAM_ZOOM_MAX,
  DIAGRAM_ZOOM_MIN,
} from "./diagramViewport";

export { DIAGRAM_ZOOM_MAX, DIAGRAM_ZOOM_MIN } from "./diagramViewport";

export const DIAGRAM_FIT_VIEW_OPTIONS: FitViewOptions = {
  padding: DIAGRAM_FIT_PADDING,
  duration: 0,
  minZoom: DIAGRAM_ZOOM_MIN,
  maxZoom: 1.35,
};

export const DIAGRAM_USER_ZOOM_EXTENT = {
  minZoom: DIAGRAM_ZOOM_MIN,
  maxZoom: DIAGRAM_ZOOM_MAX,
} as const;

/**
 * Enquadra nós de atividade, cabeçalhos de faixa e (via padding) folga das edges.
 * A largura visual da faixa acompanha os filhos — não há canvas dummy de 2400px.
 */
export function getDiagramFitNodes(nodes: Node[]): Node[] {
  return nodes;
}

/** Exportação PNG inclui cabeçalhos de faixa e altura total das swimlanes. */
export function getDiagramExportNodes(nodes: Node[]): Node[] {
  return getDiagramFitNodes(nodes);
}
