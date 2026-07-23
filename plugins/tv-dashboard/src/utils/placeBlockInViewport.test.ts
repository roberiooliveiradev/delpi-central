import { describe, expect, it } from "vitest";

import {
  placeFrameCenteredAt,
  placeFrameInViewportCenter,
  resolveViewportCenterCanvasPercent,
} from "./placeBlockInViewport";

describe("placeFrameCenteredAt", () => {
  it("centraliza o bloco no ponto e clampeia no slide", () => {
    expect(placeFrameCenteredAt({ x: 5, y: 28, w: 20, h: 10 }, { x: 50, y: 50 })).toEqual({
      x: 40,
      y: 45,
      w: 20,
      h: 10,
    });
    expect(placeFrameCenteredAt({ x: 0, y: 0, w: 40, h: 40 }, { x: 5, y: 5 })).toEqual({
      x: 0,
      y: 0,
      w: 40,
      h: 40,
    });
    expect(placeFrameCenteredAt({ x: 0, y: 0, w: 40, h: 40 }, { x: 95, y: 95 })).toEqual({
      x: 60,
      y: 60,
      w: 40,
      h: 40,
    });
  });

  it("ponto (w/h 0) fica no centro", () => {
    expect(placeFrameCenteredAt({ x: 45, y: 45, w: 0, h: 0 }, { x: 12, y: 88 })).toEqual({
      x: 12,
      y: 88,
      w: 0,
      h: 0,
    });
  });
});

describe("resolveViewportCenterCanvasPercent", () => {
  it("usa o centro do wrap em % do canvas", () => {
    const canvas = document.createElement("div");
    const wrap = document.createElement("div");
    canvas.getBoundingClientRect = () =>
      ({
        left: 100,
        top: 50,
        width: 200,
        height: 100,
        right: 300,
        bottom: 150,
        x: 100,
        y: 50,
        toJSON: () => ({}),
      }) as DOMRect;
    wrap.getBoundingClientRect = () =>
      ({
        left: 120,
        top: 60,
        width: 100,
        height: 40,
        right: 220,
        bottom: 100,
        x: 120,
        y: 60,
        toJSON: () => ({}),
      }) as DOMRect;

    expect(resolveViewportCenterCanvasPercent(canvas, wrap)).toEqual({
      x: ((170 - 100) / 200) * 100,
      y: ((80 - 50) / 100) * 100,
    });
  });

  it("sem canvas retorna null", () => {
    expect(resolveViewportCenterCanvasPercent(null)).toBeNull();
  });
});

describe("placeFrameInViewportCenter", () => {
  it("sem canvas preserva o frame", () => {
    const frame = { x: 5, y: 28, w: 12, h: 7 };
    expect(placeFrameInViewportCenter(frame, null)).toEqual(frame);
  });
});
