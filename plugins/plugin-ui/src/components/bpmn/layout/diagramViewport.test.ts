import { describe, expect, it } from "vitest";

import { getDiagramExportNodes, getDiagramFitNodes } from "./diagramViewFit";
import {
  clampDiagramZoom,
  computeFitTransform,
  computeResetTransform,
  contentBoundsFromFlowNodes,
  DIAGRAM_FIT_MAX_ZOOM,
  DIAGRAM_RESET_ZOOM,
  DIAGRAM_ZOOM_MAX,
  DIAGRAM_ZOOM_MIN,
  expandContentBounds,
  emptyContentBounds,
  panViewport,
  parseSvgWorldSize,
  unionContentBounds,
  zoomViewportAt,
} from "./diagramViewport";

const VIEWPORT = { width: 800, height: 600 };

describe("diagramViewport", () => {
  it("enquadra processo pequeno sem estourar o zoom máximo de ajuste", () => {
    const transform = computeFitTransform(
      { minX: 0, minY: 0, maxX: 400, maxY: 240 },
      VIEWPORT
    );

    expect(transform.zoom).toBeLessThanOrEqual(DIAGRAM_FIT_MAX_ZOOM);
    expect(transform.zoom).toBeGreaterThan(0.5);
  });

  it("enquadra processo grande usando os bounds reais e o minZoom seguro", () => {
    const transform = computeFitTransform(
      { minX: 0, minY: 0, maxX: 12000, maxY: 4000 },
      VIEWPORT
    );

    expect(transform.zoom).toBeGreaterThanOrEqual(DIAGRAM_ZOOM_MIN);
    expect(transform.zoom).toBeLessThan(0.2);
    const fittedWidth = 12000 * transform.zoom;
    expect(fittedWidth).toBeLessThanOrEqual(800);
  });

  it("não assume que o conteúdo começa em 0,0", () => {
    const bounds = unionContentBounds([{ x: 400, y: 220, width: 180, height: 80 }]);
    expect(bounds.minX).toBe(400);
    expect(bounds.minY).toBe(220);

    const fromEmpty = expandContentBounds(emptyContentBounds(), {
      x: 400,
      y: 220,
      width: 180,
      height: 80,
    });
    expect(fromEmpty.minX).toBe(400);
    expect(fromEmpty.minY).toBe(220);

    const transform = computeFitTransform(bounds, VIEWPORT);
    expect(transform.x).not.toBe(VIEWPORT.width / 2);
    const contentCenterX = (400 + 580) / 2;
    expect(transform.x).toBeCloseTo(VIEWPORT.width / 2 - contentCenterX * transform.zoom);
  });

  it("enquadra minX/minY negativos", () => {
    const bounds = { minX: -200, minY: -80, maxX: 120, maxY: 100 };
    const transform = computeFitTransform(bounds, VIEWPORT);
    expect(transform.zoom).toBeGreaterThan(0.5);
    expect(Number.isFinite(transform.x)).toBe(true);
    expect(Number.isFinite(transform.y)).toBe(true);
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
      VIEWPORT
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

  it("não trata SVG enorme com width 100% como world 1x1", () => {
    const size = parseSvgWorldSize(
      `<svg width="100%" height="100%" style="max-width: 6400px; height: 2200px" xmlns="http://www.w3.org/2000/svg"></svg>`
    );
    expect(size.width).toBe(6400);
    expect(size.height).toBe(2200);
  });

  it("usa viewBox quando width/height intrínsecos divergem", () => {
    const size = parseSvgWorldSize(
      `<svg width="200" height="80" viewBox="40 10 3200 1400"></svg>`
    );
    expect(size).toEqual({ width: 3200, height: 1400 });
  });

  it("fit de SVG largo/alto não aplica 135% sobre world 1x1", () => {
    const large = parseSvgWorldSize(
      `<svg width="100%" viewBox="0 0 6400 1800"></svg>`
    );
    const transform = computeFitTransform(
      { minX: 0, minY: 0, maxX: large.width, maxY: large.height },
      VIEWPORT
    );
    expect(transform.zoom).toBeLessThan(1);
    expect(transform.zoom).toBeGreaterThanOrEqual(DIAGRAM_ZOOM_MIN);
    expect(6400 * transform.zoom).toBeLessThanOrEqual(800);
  });
});

describe("contentBoundsFromFlowNodes", () => {
  it("não infla o world com a largura visual da swimlane", () => {
    const bounds = contentBoundsFromFlowNodes([
      {
        type: "lane",
        position: { x: 0, y: 0 },
        width: 8000,
        height: 900,
      },
      {
        type: "flowchart",
        position: { x: 180, y: 40 },
        width: 180,
        height: 88,
      },
      {
        type: "flowchart",
        position: { x: 420, y: 48 },
        width: 200,
        height: 88,
      },
    ]);

    expect(bounds.maxX - bounds.minX).toBeLessThan(500);
    const transform = computeFitTransform(bounds, VIEWPORT);
    expect(transform.zoom).toBeGreaterThan(0.5);
    expect(transform.zoom).not.toBeCloseTo(0.08, 1);
  });

  it("processo grande continua com bounds reais dos nós", () => {
    const bounds = contentBoundsFromFlowNodes([
      { type: "flowchart", position: { x: 180, y: 40 }, width: 180, height: 88 },
      { type: "flowchart", position: { x: 5200, y: 48 }, width: 200, height: 88 },
    ]);
    expect(bounds.maxX).toBeGreaterThan(5200);
    const transform = computeFitTransform(bounds, VIEWPORT);
    expect(transform.zoom).toBeLessThan(0.2);
  });

  it("ignora coordenadas inválidas", () => {
    const bounds = contentBoundsFromFlowNodes([
      { type: "flowchart", position: { x: Number.NaN, y: 0 }, width: 180, height: 80 },
      { type: "flowchart", position: { x: 40, y: 40 }, width: 180, height: 80 },
    ]);
    expect(bounds.minX).toBe(40);
    expect(bounds.maxX).toBe(220);
  });
});

describe("getDiagramFitNodes", () => {
  it("exclui faixas do fit do React Flow", () => {
    const nodes = [
      { id: "lane-1", type: "lane", position: { x: 0, y: 0 }, data: {}, width: 8000, height: 900 },
      { id: "n1", type: "flowchart", position: { x: 220, y: 80 }, data: {}, width: 180, height: 80 },
    ];
    expect(getDiagramFitNodes(nodes).map((node) => node.id)).toEqual(["n1"]);
    expect(getDiagramExportNodes(nodes).map((node) => node.id)).toEqual(["lane-1", "n1"]);
  });
});

describe("processo composto real 5b3dc7e3", () => {
  it("usa bounds das 106 atividades (~15k px) e não das raias visuais", async () => {
    const { PROCESS_COMPOSED_GEOMETRY, processComposedFlowNodes } = await import(
      "./fixtures/processComposedGeometry.fixture"
    );
    const nodes = processComposedFlowNodes();
    expect(nodes.filter((node) => node.type === "flowchart")).toHaveLength(
      PROCESS_COMPOSED_GEOMETRY.activityCount
    );

    const bounds = contentBoundsFromFlowNodes(nodes);
    expect(bounds.minX).toBe(PROCESS_COMPOSED_GEOMETRY.bounds.minX);
    expect(bounds.minY).toBe(PROCESS_COMPOSED_GEOMETRY.bounds.minY);
    expect(bounds.maxX).toBeGreaterThanOrEqual(PROCESS_COMPOSED_GEOMETRY.bounds.maxX);
    expect(bounds.maxY).toBeGreaterThanOrEqual(PROCESS_COMPOSED_GEOMETRY.bounds.maxY);
    expect(getDiagramFitNodes(nodes as never).every((node) => node.type !== "lane")).toBe(true);

    const compactViewport = { width: 488, height: 280 };
    const fullscreenViewport = { width: 1400, height: 800 };
    const compactFit = computeFitTransform(bounds, compactViewport);
    const fullscreenFit = computeFitTransform(bounds, fullscreenViewport);

    expect(compactFit.zoom).toBe(DIAGRAM_ZOOM_MIN);
    expect(fullscreenFit.zoom).toBeGreaterThanOrEqual(DIAGRAM_ZOOM_MIN);
    expect(fullscreenFit.zoom).toBeLessThan(0.12);
    expect(fullscreenFit.zoom).not.toBe(DIAGRAM_FIT_MAX_ZOOM);
  });
});
