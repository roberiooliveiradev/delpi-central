import { describe, expect, it } from "vitest";

import {
  buildAxisRulerTicks,
  clampStageZoom,
  computeFitStageZoom,
  shouldRenderStageGrid,
  stageZoomFromWheelDelta,
  STAGE_GRID_MIN_ZOOM,
  STAGE_RULER_UNITS,
} from "./stageViewport";

describe("stageViewport", () => {
  it("limita zoom entre 10% e 200%", () => {
    expect(clampStageZoom(0.05)).toBe(0.1);
    expect(clampStageZoom(3)).toBe(2);
    expect(clampStageZoom(1.234)).toBe(1.23);
  });

  it("calcula fit pelo menor eixo disponível", () => {
    const wrap = document.createElement("div");
    const canvas = document.createElement("div");
    Object.defineProperty(wrap, "clientWidth", { value: 300 });
    Object.defineProperty(wrap, "clientHeight", { value: 400 });
    Object.defineProperty(canvas, "offsetWidth", { value: 400 });
    Object.defineProperty(canvas, "offsetHeight", { value: 225 });
    wrap.style.padding = "10px";
    document.body.appendChild(wrap);
    document.body.appendChild(canvas);

    const zoom = computeFitStageZoom(wrap, canvas);
    expect(zoom).toBe(0.7);

    wrap.remove();
    canvas.remove();
  });

  it("gera marcas da régua com rótulos a cada 20 unidades", () => {
    const ticks = buildAxisRulerTicks(200, 2, 0, 0, STAGE_RULER_UNITS);
    const labels = ticks.filter((tick) => tick.label).map((tick) => tick.label);
    expect(labels).toContain("0");
    expect(labels).toContain("20");
    expect(labels).toContain("40");
  });

  it("oculta grade abaixo do zoom mínimo útil", () => {
    expect(shouldRenderStageGrid(true, STAGE_GRID_MIN_ZOOM)).toBe(true);
    expect(shouldRenderStageGrid(true, STAGE_GRID_MIN_ZOOM - 0.01)).toBe(false);
    expect(shouldRenderStageGrid(false, 1)).toBe(false);
  });

  it("Ctrl+scroll aproxima com deltaY negativo", () => {
    expect(stageZoomFromWheelDelta(1, -100)).toBe(1.05);
    expect(stageZoomFromWheelDelta(1, 100)).toBe(0.95);
    expect(stageZoomFromWheelDelta(0.12, 400)).toBe(0.1);
  });
});
