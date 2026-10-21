import { describe, expect, it } from "vitest";

import { clampCrop, cropPointerMode, fitCanvas, nextCrop, sourceRect } from "./referenceCrop";

describe("reference crop", () => {
  it("fits the preview canvas inside the original limit", () => {
    expect(fitCanvas(4800, 2400)).toEqual({ cw: 2400, ch: 1200, sx: 0.5, sy: 0.5 });
  });

  it("starts a new selection on the full image and moves an inner crop", () => {
    const full = { x: 0, y: 0, w: 400, h: 300 };
    expect(cropPointerMode({ x: 200, y: 150 }, full, { cw: 400, ch: 300 })).toBe("new");
    const inner = { x: 40, y: 40, w: 120, h: 80 };
    expect(cropPointerMode({ x: 80, y: 70 }, inner, { cw: 400, ch: 300 })).toBe("move");
    expect(nextCrop("move", inner, { x: 80, y: 70 }, { x: 100, y: 90 }, { cw: 400, ch: 300 })).toEqual({
      x: 60,
      y: 60,
      w: 120,
      h: 80,
    });
  });

  it("maps the canvas crop back to the source image", () => {
    const size = fitCanvas(200, 100);
    const crop = clampCrop({ x: 10, y: 10, w: 20, h: 20 }, size.cw, size.ch);
    expect(sourceRect(crop, size)).toEqual({ x: 10, y: 10, w: 20, h: 20 });
  });
});