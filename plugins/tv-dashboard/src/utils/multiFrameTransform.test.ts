import { describe, expect, it } from "vitest";

import { applyMultiFrameDelta } from "./multiFrameTransform";

describe("applyMultiFrameDelta", () => {
  it("move aplica o mesmo dx/dy a todos", () => {
    const start = new Map([
      ["a", { x: 10, y: 20, w: 30, h: 40 }],
      ["b", { x: 50, y: 60, w: 20, h: 10 }],
    ]);
    const next = applyMultiFrameDelta(start, "a", { x: 15, y: 25, w: 30, h: 40 });
    expect(next.get("a")).toEqual({ x: 15, y: 25, w: 30, h: 40 });
    expect(next.get("b")).toEqual({ x: 55, y: 65, w: 20, h: 10 });
  });

  it("resize aplica dw/dh e o deslocamento do handle (ex.: NW)", () => {
    const start = new Map([
      ["a", { x: 20, y: 20, w: 40, h: 40 }],
      ["b", { x: 70, y: 30, w: 20, h: 20 }],
    ]);
    const next = applyMultiFrameDelta(start, "a", { x: 10, y: 10, w: 50, h: 50 });
    expect(next.get("a")).toEqual({ x: 10, y: 10, w: 50, h: 50 });
    expect(next.get("b")).toEqual({ x: 60, y: 20, w: 30, h: 30 });
  });

  it("respeita único piso > 0 nos secundários", () => {
    const start = new Map([
      ["a", { x: 0, y: 0, w: 10, h: 10 }],
      ["b", { x: 20, y: 0, w: 2, h: 2 }],
    ]);
    const next = applyMultiFrameDelta(start, "a", { x: 0, y: 0, w: 5, h: 5 });
    expect(next.get("b")?.w).toBeGreaterThan(0);
    expect(next.get("b")?.h).toBeGreaterThan(0);
    expect(next.get("b")?.w).toBeLessThan(0.01);
    expect(next.get("b")?.h).toBeLessThan(0.01);
  });
});
