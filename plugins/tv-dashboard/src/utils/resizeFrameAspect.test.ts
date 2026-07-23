import { describe, expect, it } from "vitest";

import { resizeFrameWithOptionalAspect } from "./resizeFrameAspect";

describe("resizeFrameWithOptionalAspect", () => {
  const start = { x: 10, y: 20, w: 40, h: 20 }; // aspect 2

  it("sem Shift: resize livre no canto SE", () => {
    const next = resizeFrameWithOptionalAspect(start, 10, 5, "se", 2, false);
    expect(next).toEqual({ x: 10, y: 20, w: 50, h: 25 });
  });

  it("com Shift no SE: mantém proporção e âncora NW", () => {
    const next = resizeFrameWithOptionalAspect(start, 10, 0, "se", 2, true);
    expect(next.x).toBe(10);
    expect(next.y).toBe(20);
    expect(next.w).toBe(50);
    expect(next.h).toBe(25);
    expect(next.w / next.h).toBeCloseTo(2, 5);
  });

  it("com Shift no NW: âncora SE fixa", () => {
    const next = resizeFrameWithOptionalAspect(start, -10, 0, "nw", 2, true);
    expect(next.w).toBe(50);
    expect(next.h).toBe(25);
    expect(next.x + next.w).toBeCloseTo(start.x + start.w, 5);
    expect(next.y + next.h).toBeCloseTo(start.y + start.h, 5);
  });

  it("com Shift na aresta E: altura centrada", () => {
    const next = resizeFrameWithOptionalAspect(start, 20, 0, "e", 2, true);
    expect(next.w).toBe(60);
    expect(next.h).toBe(30);
    expect(next.x).toBe(10);
    expect(next.y + next.h / 2).toBeCloseTo(start.y + start.h / 2, 5);
  });

  it("aceita modo resize-se do bloco", () => {
    const next = resizeFrameWithOptionalAspect(start, 10, 0, "resize-se", 2, true);
    expect(next.w / next.h).toBeCloseTo(2, 5);
  });

  it("resize livre permite largura muito fina (> 0)", () => {
    const next = resizeFrameWithOptionalAspect(start, -39.9, 0, "e", 2, false);
    expect(next.w).toBeCloseTo(0.1, 5);
    expect(next.h).toBe(20);
    // Aresta W: dx positivo = arrastar para dentro (direita).
    const atFloor = resizeFrameWithOptionalAspect(start, 100, 0, "w", 2, false);
    expect(atFloor.w).toBeGreaterThan(0);
    expect(atFloor.w).toBeLessThan(0.01);
    expect(atFloor.x + atFloor.w).toBeCloseTo(start.x + start.w, 5);
  });
});
