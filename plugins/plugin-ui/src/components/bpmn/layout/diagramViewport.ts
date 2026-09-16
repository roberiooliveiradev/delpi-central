export const DIAGRAM_ZOOM_MIN = 0.05;
export const DIAGRAM_ZOOM_MAX = 3;
export const DIAGRAM_ZOOM_STEP = 0.1;
export const DIAGRAM_FIT_PADDING = 0.12;
export const DIAGRAM_RESET_ZOOM = 1;
export const DIAGRAM_FIT_MAX_ZOOM = 1.35;

export type DiagramViewportTransform = {
  x: number;
  y: number;
  zoom: number;
};

export type DiagramContentBounds = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
};

export type DiagramViewportSize = {
  width: number;
  height: number;
};

export type DiagramFitNodeLike = {
  type?: string;
  position: { x: number; y: number };
  width?: number | null;
  height?: number | null;
  measured?: { width?: number; height?: number } | null;
};

export function clampDiagramZoom(zoom: number): number {
  if (!Number.isFinite(zoom)) {
    return DIAGRAM_RESET_ZOOM;
  }
  return Math.min(DIAGRAM_ZOOM_MAX, Math.max(DIAGRAM_ZOOM_MIN, zoom));
}

export function emptyContentBounds(): DiagramContentBounds {
  return { minX: Number.POSITIVE_INFINITY, minY: Number.POSITIVE_INFINITY, maxX: Number.NEGATIVE_INFINITY, maxY: Number.NEGATIVE_INFINITY };
}

export function isFiniteContentBounds(bounds: DiagramContentBounds): boolean {
  return [bounds.minX, bounds.minY, bounds.maxX, bounds.maxY].every(Number.isFinite);
}

export function contentSize(bounds: DiagramContentBounds): { width: number; height: number } {
  if (!isFiniteContentBounds(bounds)) {
    return { width: 1, height: 1 };
  }
  return {
    width: Math.max(1, bounds.maxX - bounds.minX),
    height: Math.max(1, bounds.maxY - bounds.minY),
  };
}

function isValidBox(box: { x: number; y: number; width: number; height: number }): boolean {
  return (
    Number.isFinite(box.x) &&
    Number.isFinite(box.y) &&
    Number.isFinite(box.width) &&
    Number.isFinite(box.height) &&
    box.width > 0 &&
    box.height > 0
  );
}

export function expandContentBounds(
  bounds: DiagramContentBounds,
  box: { x: number; y: number; width: number; height: number }
): DiagramContentBounds {
  if (!isValidBox(box)) {
    return bounds;
  }
  return {
    minX: Math.min(bounds.minX, box.x),
    minY: Math.min(bounds.minY, box.y),
    maxX: Math.max(bounds.maxX, box.x + box.width),
    maxY: Math.max(bounds.maxY, box.y + box.height),
  };
}

export function unionContentBounds(
  boxes: Array<{ x: number; y: number; width: number; height: number }>
): DiagramContentBounds {
  let bounds = emptyContentBounds();
  for (const box of boxes) {
    bounds = expandContentBounds(bounds, box);
  }
  if (!isFiniteContentBounds(bounds)) {
    return { minX: 0, minY: 0, maxX: 1, maxY: 1 };
  }
  return bounds;
}

/**
 * Bounds de enquadramento no espaço WORLD.
 * Faixas visuais (autosize) não entram — a largura da raia copiaria x global dos filhos
 * e inflaria o zoom para ~8% em processos longos.
 */
export function contentBoundsFromFlowNodes(nodes: DiagramFitNodeLike[]): DiagramContentBounds {
  const boxes: Array<{ x: number; y: number; width: number; height: number }> = [];
  for (const node of nodes) {
    if (node.type === "lane") continue;
    const x = node.position?.x;
    const y = node.position?.y;
    if (!Number.isFinite(x) || !Number.isFinite(y)) continue;
    const width = node.measured?.width ?? node.width ?? 180;
    const height = node.measured?.height ?? node.height ?? 80;
    if (!Number.isFinite(width) || !Number.isFinite(height) || width <= 0 || height <= 0) continue;
    boxes.push({ x, y, width, height });
  }
  return unionContentBounds(boxes);
}

export function computeFitTransform(
  bounds: DiagramContentBounds,
  viewport: DiagramViewportSize,
  options?: { padding?: number; minZoom?: number; maxZoom?: number }
): DiagramViewportTransform {
  const padding = options?.padding ?? DIAGRAM_FIT_PADDING;
  const minZoom = options?.minZoom ?? DIAGRAM_ZOOM_MIN;
  const maxZoom = options?.maxZoom ?? DIAGRAM_FIT_MAX_ZOOM;
  const size = contentSize(bounds);
  const availableWidth = Math.max(1, viewport.width * (1 - padding * 2));
  const availableHeight = Math.max(1, viewport.height * (1 - padding * 2));
  const zoom = clampDiagramZoom(
    Math.min(maxZoom, Math.max(minZoom, Math.min(availableWidth / size.width, availableHeight / size.height)))
  );
  const x = viewport.width / 2 - (bounds.minX + size.width / 2) * zoom;
  const y = viewport.height / 2 - (bounds.minY + size.height / 2) * zoom;
  return { x, y, zoom };
}

export function computeResetTransform(
  bounds: DiagramContentBounds,
  viewport: DiagramViewportSize
): DiagramViewportTransform {
  const size = contentSize(bounds);
  return {
    x: viewport.width / 2 - (bounds.minX + size.width / 2) * DIAGRAM_RESET_ZOOM,
    y: viewport.height / 2 - (bounds.minY + size.height / 2) * DIAGRAM_RESET_ZOOM,
    zoom: DIAGRAM_RESET_ZOOM,
  };
}

export function panViewport(
  transform: DiagramViewportTransform,
  deltaX: number,
  deltaY: number
): DiagramViewportTransform {
  return {
    ...transform,
    x: transform.x + deltaX,
    y: transform.y + deltaY,
  };
}

export function zoomViewportAt(
  transform: DiagramViewportTransform,
  nextZoom: number,
  anchor: { x: number; y: number }
): DiagramViewportTransform {
  const zoom = clampDiagramZoom(nextZoom);
  const ratio = zoom / (transform.zoom || DIAGRAM_RESET_ZOOM);
  return {
    x: anchor.x - (anchor.x - transform.x) * ratio,
    y: anchor.y - (anchor.y - transform.y) * ratio,
    zoom,
  };
}

export function parseSvgWorldSize(svg: string): { width: number; height: number } {
  const source = firstSvgOpenTag(String(svg || ""));
  const viewBox = parseViewBoxSize(source);
  if (viewBox) {
    return viewBox;
  }

  const width =
    parseSvgLength(source.match(/\bwidth=["']([^"']+)["']/i)?.[1]) ??
    parseSvgLength(source.match(/max-width:\s*([0-9.]+)px/i)?.[1]) ??
    parseSvgLength(source.match(/(?:^|[^-])width:\s*([0-9.]+)px/i)?.[1]);
  const height =
    parseSvgLength(source.match(/\bheight=["']([^"']+)["']/i)?.[1]) ??
    parseSvgLength(source.match(/max-height:\s*([0-9.]+)px/i)?.[1]) ??
    parseSvgLength(source.match(/(?:^|[^-])height:\s*([0-9.]+)px/i)?.[1]);
  if (width && height) {
    return { width, height };
  }

  return { width: 1, height: 1 };
}

export function measureSvgWorldSize(svg: SVGSVGElement): { width: number; height: number } {
  const parsed = parseSvgWorldSize(svg.outerHTML);
  try {
    if (typeof svg.getBBox === "function") {
      const bbox = svg.getBBox();
      if (bbox && bbox.width > 1 && bbox.height > 1) {
        return {
          width: Math.max(parsed.width, bbox.width),
          height: Math.max(parsed.height, bbox.height),
        };
      }
    }
  } catch {
    /* jsdom / SVG not rendered */
  }
  return parsed;
}

function firstSvgOpenTag(source: string): string {
  const match = source.match(/<svg\b[^>]*>/i);
  return match?.[0] ?? source;
}

function parseViewBoxSize(source: string): { width: number; height: number } | null {
  const viewBoxMatch = source.match(/viewBox=["']([^"']+)["']/i);
  if (!viewBoxMatch) return null;
  const parts = viewBoxMatch[1].trim().split(/[\s,]+/).map(Number);
  if (parts.length === 4 && parts.every(Number.isFinite) && parts[2] > 0 && parts[3] > 0) {
    return { width: parts[2], height: parts[3] };
  }
  return null;
}

function parseSvgLength(value: string | undefined): number | null {
  if (!value || /%/.test(value)) {
    return null;
  }
  const parsed = Number.parseFloat(String(value).replace(/[^\d.-]/g, ""));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
