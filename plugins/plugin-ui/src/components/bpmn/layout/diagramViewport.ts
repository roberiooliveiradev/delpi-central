export const DIAGRAM_ZOOM_MIN = 0.05;
export const DIAGRAM_ZOOM_MAX = 3;
export const DIAGRAM_ZOOM_STEP = 0.1;
export const DIAGRAM_FIT_PADDING = 0.12;
export const DIAGRAM_RESET_ZOOM = 1;

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

export function clampDiagramZoom(zoom: number): number {
  if (!Number.isFinite(zoom)) {
    return DIAGRAM_RESET_ZOOM;
  }
  return Math.min(DIAGRAM_ZOOM_MAX, Math.max(DIAGRAM_ZOOM_MIN, zoom));
}

export function emptyContentBounds(): DiagramContentBounds {
  return { minX: 0, minY: 0, maxX: 0, maxY: 0 };
}

export function contentSize(bounds: DiagramContentBounds): { width: number; height: number } {
  return {
    width: Math.max(1, bounds.maxX - bounds.minX),
    height: Math.max(1, bounds.maxY - bounds.minY),
  };
}

export function expandContentBounds(
  bounds: DiagramContentBounds,
  box: { x: number; y: number; width: number; height: number }
): DiagramContentBounds {
  return {
    minX: Math.min(bounds.minX, box.x),
    minY: Math.min(bounds.minY, box.y),
    maxX: Math.max(bounds.maxX, box.x + box.width),
    maxY: Math.max(bounds.maxY, box.y + box.height),
  };
}

export function computeFitTransform(
  bounds: DiagramContentBounds,
  viewport: DiagramViewportSize,
  options?: { padding?: number; minZoom?: number; maxZoom?: number }
): DiagramViewportTransform {
  const padding = options?.padding ?? DIAGRAM_FIT_PADDING;
  const minZoom = options?.minZoom ?? DIAGRAM_ZOOM_MIN;
  const maxZoom = options?.maxZoom ?? 1.35;
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
  const ratio = zoom / transform.zoom;
  return {
    x: anchor.x - (anchor.x - transform.x) * ratio,
    y: anchor.y - (anchor.y - transform.y) * ratio,
    zoom,
  };
}

export function parseSvgWorldSize(svg: string): { width: number; height: number } {
  const source = String(svg || "");
  const viewBoxMatch = source.match(/viewBox=["']([^"']+)["']/i);
  if (viewBoxMatch) {
    const parts = viewBoxMatch[1].trim().split(/[\s,]+/).map(Number);
    if (parts.length === 4 && parts.every(Number.isFinite) && parts[2] > 0 && parts[3] > 0) {
      return { width: parts[2], height: parts[3] };
    }
  }

  const width = parseSvgLength(source.match(/\bwidth=["']([^"']+)["']/i)?.[1]);
  const height = parseSvgLength(source.match(/\bheight=["']([^"']+)["']/i)?.[1]);
  if (width && height) {
    return { width, height };
  }

  return { width: 1, height: 1 };
}

function parseSvgLength(value: string | undefined): number | null {
  if (!value || /%/.test(value)) {
    return null;
  }
  const parsed = Number.parseFloat(value.replace(/[^\d.-]/g, ""));
  return Number.isFinite(parsed) && parsed > 0 ? parsed : null;
}
