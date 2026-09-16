import { describe, expect, it } from "vitest";

import {
  clampDiagramZoom,
  computeFitTransform,
  computeResetTransform,
  DIAGRAM_RESET_ZOOM,
  DIAGRAM_ZOOM_MAX,
  DIAGRAM_ZOOM_MIN,
  panViewport,
  parseSvgWorldSize,
  zoomViewportAt,
} from "./diagramViewport";

describe("diagramViewport", () => {
  it("enquadra processo pequeno sem estourar o zoom máximo de ajuste", () => {
    const transform = computeFitTransform(
      { minX: 0, minY: 0, maxX: 400, maxY: 240 },
      { width: 800, height: 600 }
    );

    expect(transform.zoom).toBeLessThanOrEqual(1.35);
    expect(transform.zoom).toBeGreaterThan(0.5);
  });

  it("enquadra processo grande usando os bounds reais e o minZoom seguro", () => {
    const transform = computeFitTransform(
      { minX: 0, minY: 0, maxX: 12000, maxY: 4000 },
      { width: 800, height: 600 }
    );

    expect(transform.zoom).toBeGreaterThanOrEqual(DIAGRAM_ZOOM_MIN);
    expect(transform.zoom).toBeLessThan(0.2);
    const fittedWidth = 12000 * transform.zoom;
    expect(fittedWidth).toBeLessThanOrEqual(800);
  });

  it("recalcula o enquadramento quando o container muda de tamanho", () => {
    const bounds = { minX: 0, minY: 0, maxX: 2000, maxY: 1000 };
    const compact = computeFitTransform(bounds, { width: 400, height: 300 });
    const wide = computeFitTransform(bounds, { width: 1200, height: 900 });

    expect(wide.zoom).toBeGreaterThan(compact.zoom);
  });

  it("limita zoom in/out", () => {
    expect(clampDiagramZoom(0.001)).toBe(DIAGRAM_ZOOM_MIN);
    expect(clampDiagramZoom(99)).toBe(DIAGRAM_ZOOM_MAX);
    expect(clampDiagramZoom(1)).toBe(1);
  });

  it("pan não altera um modelo canônico", () => {
    const flowchart = {
      format: "flowchart_v1" as const,
      format_version: 1,
      nodes: [{ id: "n1", type: "start" as const, label: "Início", position: { x: 40, y: 40 } }],
      edges: [],
    };
    const snapshot = structuredClone(flowchart);
    const next = panViewport({ x: 10, y: 20, zoom: 1 }, 40, -15);

    expect(next).toEqual({ x: 50, y: 5, zoom: 1 });
    expect(flowchart).toEqual(snapshot);
  });

  it("reset volta a 100%", () => {
    const transform = computeResetTransform(
      { minX: 0, minY: 0, maxX: 400, maxY: 200 },
      { width: 800, height: 600 }
    );
    expect(transform.zoom).toBe(DIAGRAM_RESET_ZOOM);
  });

  it("zoom no ponto âncora mantém o mundo sob o cursor", () => {
    const current = { x: 0, y: 0, zoom: 1 };
    const next = zoomViewportAt(current, 2, { x: 100, y: 50 });
    expect(next.zoom).toBe(2);
    expect(next.x).toBe(-100);
    expect(next.y).toBe(-50);
  });

  it("lê o tamanho do SVG pelo viewBox mesmo com width percentual", () => {
    const size = parseSvgWorldSize(
      `<svg width="100%" height="100%" viewBox="0 0 4800 1600"></svg>`
    );
    expect(size).toEqual({ width: 4800, height: 1600 });
  });
});
