import { describe, expect, it } from "vitest";

import {
  applyGroupRotationDelta,
  resolveFramesGroupCenter,
  resolveGroupSelectionChrome,
  rotatePointPercentAround,
} from "./slidePercentRotation";

describe("rotatePointPercentAround", () => {
  it("com aspect 1, 90° mapeia eixo X→Y como antes", () => {
    const next = rotatePointPercentAround({ x: 10, y: 50 }, { x: 50, y: 50 }, 90, 1);
    expect(next.x).toBeCloseTo(50, 5);
    expect(next.y).toBeCloseTo(10, 5);
  });

  it("com aspect 16/9, 90° preserva distância visual (px)", () => {
    const aspect = 16 / 9;
    const next = rotatePointPercentAround({ x: 10, y: 50 }, { x: 50, y: 50 }, 90, aspect);
    expect(next.x).toBeCloseTo(50, 5);
    expect(next.y).toBeCloseTo(50 - 40 * aspect, 5);
  });
});

describe("applyGroupRotationDelta", () => {
  it("orbita membros em torno do centro e soma rotação (aspect 1)", () => {
    const startFrames = new Map([
      ["a", { x: 0, y: 40, w: 20, h: 20 }],
      ["b", { x: 80, y: 40, w: 20, h: 20 }],
    ]);
    const startRotations = new Map([
      ["a", 0],
      ["b", 10],
    ]);
    const center = resolveFramesGroupCenter(startFrames.values());
    expect(center).toEqual({ x: 50, y: 50 });

    const next = applyGroupRotationDelta({
      startFrames,
      startRotations,
      center,
      deltaDeg: 90,
      slideAspect: 1,
    });
    const a = next.get("a")!;
    const b = next.get("b")!;
    expect(a.rotation).toBe(90);
    expect(b.rotation).toBe(100);
    expect(a.frame.x + a.frame.w / 2).toBeCloseTo(50, 5);
    expect(a.frame.y + a.frame.h / 2).toBeCloseTo(10, 5);
    expect(b.frame.x + b.frame.w / 2).toBeCloseTo(50, 5);
    expect(b.frame.y + b.frame.h / 2).toBeCloseTo(90, 5);
  });

  it("com aspect 16/9 não usa y% isotrópico (evita membros ‘saindo’)", () => {
    const aspect = 16 / 9;
    const startFrames = new Map([
      ["a", { x: 0, y: 40, w: 20, h: 20 }],
      ["b", { x: 80, y: 40, w: 20, h: 20 }],
    ]);
    const startRotations = new Map([
      ["a", 0],
      ["b", 0],
    ]);
    const center = resolveFramesGroupCenter(startFrames.values());
    const next = applyGroupRotationDelta({
      startFrames,
      startRotations,
      center,
      deltaDeg: 90,
      slideAspect: aspect,
    });
    const aY = next.get("a")!.frame.y + next.get("a")!.frame.h / 2;
    expect(aY).toBeCloseTo(50 - 40 * aspect, 5);
  });
});

describe("resolveGroupSelectionChrome", () => {
  it("membro único com rotação: frame local + rotation no chrome", () => {
    const chrome = resolveGroupSelectionChrome({
      members: [{ frame: { x: 20, y: 30, w: 40, h: 40 }, rotation: 35 }],
      slideAspect: 16 / 9,
    });
    expect(chrome.rotation).toBe(35);
    expect(chrome.frame).toEqual({ x: 20, y: 30, w: 40, h: 40 });
  });

  it("rotações distintas: AABB sem rotate no overlay", () => {
    const chrome = resolveGroupSelectionChrome({
      members: [
        { frame: { x: 0, y: 0, w: 20, h: 20 }, rotation: 10 },
        { frame: { x: 40, y: 0, w: 20, h: 20 }, rotation: 40 },
      ],
    });
    expect(chrome.rotation).toBe(0);
    expect(chrome.frame).toEqual({ x: 0, y: 0, w: 60, h: 20 });
  });

  it("mesma rotação em grupo: recupera bbox local para o overlay rotacionar", () => {
    const aspect = 1;
    const startFrames = new Map([
      ["a", { x: 0, y: 40, w: 20, h: 20 }],
      ["b", { x: 80, y: 40, w: 20, h: 20 }],
    ]);
    const center = resolveFramesGroupCenter(startFrames.values());
    const rotated = applyGroupRotationDelta({
      startFrames,
      startRotations: new Map([
        ["a", 0],
        ["b", 0],
      ]),
      center,
      deltaDeg: 90,
      slideAspect: aspect,
    });
    const members = [...rotated.entries()].map(([, update]) => ({
      frame: update.frame,
      rotation: update.rotation,
    }));
    const chrome = resolveGroupSelectionChrome({ members, slideAspect: aspect });
    expect(chrome.rotation).toBe(90);
    expect(chrome.frame.x).toBeCloseTo(0, 5);
    expect(chrome.frame.y).toBeCloseTo(40, 5);
    expect(chrome.frame.w).toBeCloseTo(100, 5);
    expect(chrome.frame.h).toBeCloseTo(20, 5);
  });
});
